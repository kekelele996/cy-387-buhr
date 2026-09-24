from datetime import datetime

from django.db import transaction

from app.constants.enums import (
    CONTRACT_STATUS_RENEWED,
    LANDLORD_ROLE,
    RENEWAL_ACTION_ACCEPT,
    RENEWAL_ACTION_CONFIRM,
    RENEWAL_ACTION_COUNTER,
    RENEWAL_ACTION_CREATE,
    RENEWAL_ACTION_REJECT,
    RENEWAL_ACTION_TENANT_CANCEL,
    RENEWAL_OPEN_STATUS,
    RENEWAL_STATUS_CANCELED,
    RENEWAL_STATUS_PENDING_LANDLORD,
    RENEWAL_STATUS_PENDING_TENANT,
    RENEWAL_STATUS_RENEWED,
    TENANT_ROLE,
    VALID_CONTRACT_STATUS,
)
from app.constants.errors import ERROR_CODES, ERROR_MESSAGES
from app.utils.exceptions import AppError
from app.utils.logger import get_logger
from .models import Contract, Renewal, RenewalEvent

logger = get_logger('contract')

ACTION_ACCEPT = 'accept'
ACTION_COUNTER = 'counter'
ACTION_REJECT = 'reject'
ACTION_CONFIRM = 'confirm'
ACTION_CANCEL = 'cancel'


def _get_contract(contract_id):
    try:
        return Contract.objects.get(pk=contract_id)
    except Contract.DoesNotExist:
        raise AppError(ERROR_CODES['CONTRACT_NOT_FOUND'], ERROR_MESSAGES['CONTRACT_NOT_FOUND'], 404)


def _get_renewal(renewal_id):
    try:
        return Renewal.objects.select_related('contract').get(pk=renewal_id)
    except Renewal.DoesNotExist:
        raise AppError(ERROR_CODES['RENEWAL_NOT_FOUND'], ERROR_MESSAGES['RENEWAL_NOT_FOUND'], 404)


def _require_role(role):
    if role not in (LANDLORD_ROLE, TENANT_ROLE):
        raise AppError(ERROR_CODES['INVALID_ROLE'], ERROR_MESSAGES['INVALID_ROLE'])
    return role


def _parse_date(value):
    if isinstance(value, datetime):
        return value.date()
    if hasattr(value, 'isoformat'):
        return value
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        raise AppError(ERROR_CODES['INVALID_RENEWAL_TERM'], ERROR_MESSAGES['INVALID_RENEWAL_TERM'])


def _log_event(renewal, actor_role, action, rent=None, note=''):
    """每次处理都留下角色和时间。"""
    event = RenewalEvent.objects.create(
        renewal=renewal, actor_role=actor_role, action=action, rent=rent, note=note
    )
    logger.info(
        '续租协商 id=%s 合同 id=%s %s %s rent=%s',
        renewal.id, renewal.contract_id, actor_role, action, rent,
    )
    return event


def _overlapping_contracts(contract, start_date, end_date):
    """同一房源、其他有效合同与新租期 [start_date, end_date] 的重叠记录。"""
    return (
        Contract.objects.filter(
            property_id=contract.property_id,
            status__in=VALID_CONTRACT_STATUS,
            start_date__lte=end_date,
            end_date__gte=start_date,
        )
        .exclude(pk=contract.id)
    )


def _conflict_error(renewal, start_date, end_date):
    conflicts = [
        {
            'contractId': item.id,
            'tenantName': item.tenant_name,
            'startDate': item.start_date.isoformat(),
            'endDate': item.end_date.isoformat(),
        }
        for item in _overlapping_contracts(renewal.contract, start_date, end_date)
    ]
    detail = '；'.join(
        f"合同 {item['contractId']}（租客 {item['tenantName']}，{item['startDate']} ~ {item['endDate']}）"
        for item in conflicts
    )
    message = ERROR_MESSAGES['RENEWAL_CONFLICT']
    if detail:
        message = f'{message}：{detail}'
    return AppError(
        ERROR_CODES['RENEWAL_CONFLICT'],
        message,
        409,
        extra={'conflicts': conflicts},
    )


def create_renewal(contract_id, payload, actor_role=TENANT_ROLE):
    """租客从合同卡片发起续租，填写新租期和期望月租。"""
    _require_role(actor_role)
    if actor_role != TENANT_ROLE:
        raise AppError(ERROR_CODES['INVALID_ROLE'], '只有租客可以发起续租')

    contract = _get_contract(contract_id)

    # 已续租的合同不再更改
    if contract.status == CONTRACT_STATUS_RENEWED:
        raise AppError(
            ERROR_CODES['CONTRACT_ALREADY_RENEWED'],
            ERROR_MESSAGES['CONTRACT_ALREADY_RENEWED'],
        )
    if contract.status not in VALID_CONTRACT_STATUS:
        raise AppError(
            ERROR_CODES['CONTRACT_NOT_RENEWABLE'], ERROR_MESSAGES['CONTRACT_NOT_RENEWABLE']
        )
    # 同一合同同时只能有一个进行中的协商，避免一房多诺
    if Renewal.objects.filter(contract=contract, status__in=RENEWAL_OPEN_STATUS).exists():
        raise AppError(
            ERROR_CODES['ACTIVE_RENEWAL_EXISTS'], ERROR_MESSAGES['ACTIVE_RENEWAL_EXISTS'], 409
        )

    start_date = _parse_date(payload.get('startDate'))
    end_date = _parse_date(payload.get('endDate'))
    expected_rent = payload.get('expectedRent')
    if (
        end_date <= start_date
        or start_date < contract.end_date
        or not isinstance(expected_rent, int)
        or expected_rent <= 0
    ):
        raise AppError(
            ERROR_CODES['INVALID_RENEWAL_TERM'], ERROR_MESSAGES['INVALID_RENEWAL_TERM']
        )

    with transaction.atomic():
        renewal = Renewal.objects.create(
            contract=contract,
            start_date=start_date,
            end_date=end_date,
            rent=expected_rent,
            expected_rent=expected_rent,
            status=RENEWAL_STATUS_PENDING_LANDLORD,
        )
        _log_event(
            renewal, TENANT_ROLE, RENEWAL_ACTION_CREATE, rent=expected_rent,
            note=f'新租期 {start_date.isoformat()} ~ {end_date.isoformat()}',
        )
    return renewal


def respond_renewal(renewal_id, payload, actor_role=LANDLORD_ROLE):
    """房东处理续租：接受、还价或拒绝。"""
    _require_role(actor_role)
    if actor_role != LANDLORD_ROLE:
        raise AppError(ERROR_CODES['INVALID_ROLE'], '只有房东可以处理续租申请')

    renewal = _get_renewal(renewal_id)
    if renewal.status in (RENEWAL_STATUS_RENEWED, RENEWAL_STATUS_CANCELED):
        raise AppError(
            ERROR_CODES['RENEWAL_STATUS_FINISHED'], ERROR_MESSAGES['RENEWAL_STATUS_FINISHED']
        )
    if renewal.status != RENEWAL_STATUS_PENDING_LANDLORD:
        raise AppError(
            ERROR_CODES['RENEWAL_STATUS_MISMATCH'], ERROR_MESSAGES['RENEWAL_STATUS_MISMATCH']
        )

    action = payload.get('action')
    with transaction.atomic():
        if action == ACTION_ACCEPT:
            # 接受前同样校验同一房源的租期冲突，并说明冲突
            conflicts = _overlapping_contracts(renewal.contract, renewal.start_date, renewal.end_date)
            if conflicts.exists():
                raise _conflict_error(renewal, renewal.start_date, renewal.end_date)
            _complete_renewal(renewal, LANDLORD_ROLE, RENEWAL_ACTION_ACCEPT)

        elif action == ACTION_COUNTER:
            counter_rent = payload.get('rent')
            if not isinstance(counter_rent, int) or counter_rent <= 0:
                raise AppError(
                    ERROR_CODES['COUNTER_RENT_REQUIRED'], ERROR_MESSAGES['COUNTER_RENT_REQUIRED']
                )
            renewal.rent = counter_rent
            renewal.status = RENEWAL_STATUS_PENDING_TENANT
            renewal.save(update_fields=['rent', 'status', 'updated_at'])
            _log_event(renewal, LANDLORD_ROLE, RENEWAL_ACTION_COUNTER, rent=counter_rent)

        elif action == ACTION_REJECT:
            renewal.status = RENEWAL_STATUS_CANCELED
            renewal.save(update_fields=['status', 'updated_at'])
            _log_event(renewal, LANDLORD_ROLE, RENEWAL_ACTION_REJECT, rent=renewal.rent)

        else:
            raise AppError(
                ERROR_CODES['INVALID_RENEWAL_ACTION'],
                f"{ERROR_MESSAGES['INVALID_RENEWAL_ACTION']}：{action}",
            )
    return renewal


def confirm_renewal(renewal_id, payload, actor_role=TENANT_ROLE):
    """还价后由租客确认接受，或租客主动取消。"""
    _require_role(actor_role)
    if actor_role != TENANT_ROLE:
        raise AppError(ERROR_CODES['INVALID_ROLE'], '只有租客可以确认还价结果')

    renewal = _get_renewal(renewal_id)
    if renewal.status in (RENEWAL_STATUS_RENEWED, RENEWAL_STATUS_CANCELED):
        raise AppError(
            ERROR_CODES['RENEWAL_STATUS_FINISHED'], ERROR_MESSAGES['RENEWAL_STATUS_FINISHED']
        )

    action = payload.get('action')
    with transaction.atomic():
        if action == ACTION_CONFIRM:
            if renewal.status != RENEWAL_STATUS_PENDING_TENANT:
                raise AppError(
                    ERROR_CODES['RENEWAL_STATUS_MISMATCH'], ERROR_MESSAGES['RENEWAL_STATUS_MISMATCH']
                )
            # 确认时必须说明与同一房源其他有效合同的租期冲突
            conflicts = _overlapping_contracts(renewal.contract, renewal.start_date, renewal.end_date)
            if conflicts.exists():
                raise _conflict_error(renewal, renewal.start_date, renewal.end_date)
            _complete_renewal(renewal, TENANT_ROLE, RENEWAL_ACTION_CONFIRM)

        elif action == ACTION_CANCEL:
            if renewal.status not in RENEWAL_OPEN_STATUS:
                raise AppError(
                    ERROR_CODES['RENEWAL_STATUS_MISMATCH'], ERROR_MESSAGES['RENEWAL_STATUS_MISMATCH']
                )
            renewal.status = RENEWAL_STATUS_CANCELED
            renewal.save(update_fields=['status', 'updated_at'])
            _log_event(renewal, TENANT_ROLE, RENEWAL_ACTION_TENANT_CANCEL, rent=renewal.rent)

        else:
            raise AppError(
                ERROR_CODES['INVALID_RENEWAL_ACTION'],
                f"{ERROR_MESSAGES['INVALID_RENEWAL_ACTION']}：{action}",
            )
    return renewal


def _complete_renewal(renewal, actor_role, action):
    """续租成功：旧合同标记已续租（不再更改），生成下一份合同。"""
    old_contract = renewal.contract
    _log_event(
        renewal, actor_role, action, rent=renewal.rent,
        note='接受当前月租，续租成立' if action == RENEWAL_ACTION_ACCEPT else '租客确认接受还价，续租成立',
    )
    new_contract = Contract.objects.create(
        property=old_contract.property,
        tenant_name=old_contract.tenant_name,
        landlord_name=old_contract.landlord_name,
        rent=renewal.rent,
        start_date=renewal.start_date,
        end_date=renewal.end_date,
        status='生效中',
        renewed_from=old_contract,
    )
    old_contract.status = CONTRACT_STATUS_RENEWED
    old_contract.save(update_fields=['status'])
    renewal.status = RENEWAL_STATUS_RENEWED
    renewal.new_contract = new_contract
    renewal.save(update_fields=['status', 'new_contract', 'updated_at'])
    logger.info('续租成功：旧合同 id=%s -> 新合同 id=%s', old_contract.id, new_contract.id)
