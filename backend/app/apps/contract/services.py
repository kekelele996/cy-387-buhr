"""续租协商业务逻辑：状态流转、角色校验、租期冲突检测与新合同生成。"""

from datetime import date

from django.db import transaction

from app.apps.contract.models import Contract, RenewalEvent, RenewalRequest
from app.constants.enums import (
    CONTRACT_OCCUPYING_STATUSES,
    CONTRACT_STATUS_ACTIVE,
    CONTRACT_STATUS_RENEWED,
    RENEWAL_STATUS_CANCELLED,
    RENEWAL_STATUS_PENDING_LANDLORD,
    RENEWAL_STATUS_PENDING_TENANT,
    RENEWAL_STATUS_RENEWED,
    ROLE_LANDLORD,
    ROLE_TENANT,
)
from app.utils.exception_handler import BusinessError
from app.utils.logger import get_logger

logger = get_logger('renewal')

ACTIVE_RENEWAL_STATUSES = (RENEWAL_STATUS_PENDING_LANDLORD, RENEWAL_STATUS_PENDING_TENANT)


def _parse_date(raw, field):
    if not raw:
        raise BusinessError('RENEWAL_INVALID_INPUT', data={'field': field})
    try:
        return date.fromisoformat(raw)
    except (TypeError, ValueError):
        raise BusinessError('RENEWAL_INVALID_INPUT', data={'field': field})


def _parse_rent(raw, field):
    try:
        rent = int(raw)
    except (TypeError, ValueError):
        raise BusinessError('RENEWAL_INVALID_INPUT', data={'field': field})
    if rent <= 0:
        raise BusinessError('RENEWAL_INVALID_INPUT', data={'field': field})
    return rent


def get_contract_or_404(contract_id):
    try:
        return Contract.objects.select_related('property').get(pk=contract_id)
    except Contract.DoesNotExist:
        raise BusinessError('CONTRACT_NOT_FOUND', status_code=404)


def get_renewal_or_404(renewal_id):
    try:
        return RenewalRequest.objects.select_related('contract', 'property').get(pk=renewal_id)
    except RenewalRequest.DoesNotExist:
        raise BusinessError('RENEWAL_NOT_FOUND', status_code=404)


def _assert_not_finished(renewal):
    """已续租/已取消的协商不再允许更改。"""
    if renewal.status not in ACTIVE_RENEWAL_STATUSES:
        raise BusinessError('RENEWAL_STATE_INVALID', data={'status': renewal.status})


def _assert_actor(renewal, role, name, expect_role):
    if role != expect_role:
        raise BusinessError('RENEWAL_FORBIDDEN', data={'expectedRole': expect_role})
    expected_name = renewal.landlord_name if expect_role == ROLE_LANDLORD else renewal.tenant_name
    if name != expected_name:
        raise BusinessError('RENEWAL_FORBIDDEN', data={'expectedName': expected_name})


def _add_event(renewal, role, name, action, note=''):
    return RenewalEvent.objects.create(
        renewal=renewal, actor_role=role, actor_name=name, action=action, note=note,
    )


def find_overlapping_contracts(property_id, start, end, exclude_contract_id=None):
    """同一房源、租期 [start, end) 重叠且仍有效的其他合同。"""
    queryset = Contract.objects.filter(
        property_id=property_id,
        status__in=CONTRACT_OCCUPYING_STATUSES,
        start_date__lt=end,
        end_date__gt=start,
    )
    if exclude_contract_id is not None:
        queryset = queryset.exclude(pk=exclude_contract_id)
    return list(queryset)


def _conflict_payload(conflicts):
    return [
        {
            'id': c.id,
            'tenantName': c.tenant_name,
            'startDate': c.start_date.strftime('%Y-%m-%d'),
            'endDate': c.end_date.strftime('%Y-%m-%d'),
            'rent': c.rent,
        }
        for c in conflicts
    ]


def _ensure_no_conflict(renewal, role, name):
    """确认/接受前的租期冲突检查；冲突时记录流水并说明冲突合同。"""
    conflicts = find_overlapping_contracts(
        renewal.property_id, renewal.new_start_date, renewal.new_end_date,
        exclude_contract_id=renewal.contract_id,
    )
    if conflicts:
        note = '；'.join(
            f"与合同#{c.id}（{c.tenant_name} {c.start_date:%Y-%m-%d}~{c.end_date:%Y-%m-%d}）重叠"
            for c in conflicts
        )
        _add_event(renewal, role, name, '租期冲突', note)
        logger.warning('续租#%s 租期冲突：%s', renewal.id, note)
        raise BusinessError(
            'RENEWAL_CONFLICT', status_code=409, data={'conflicts': _conflict_payload(conflicts)},
        )


def _complete_renewal(renewal, role, name, confirm_action):
    """接受/确认成功：生成下一份合同，原合同转为已续租。"""
    with transaction.atomic():
        new_contract = Contract.objects.create(
            property=renewal.property,
            tenant_name=renewal.tenant_name,
            landlord_name=renewal.landlord_name,
            rent=renewal.proposed_rent,
            deposit=renewal.contract.deposit,
            start_date=renewal.new_start_date,
            end_date=renewal.new_end_date,
            status=CONTRACT_STATUS_ACTIVE,
        )
        old = renewal.contract
        old.status = CONTRACT_STATUS_RENEWED
        old.renewed_contract = new_contract
        old.save(update_fields=['status', 'renewed_contract'])

        renewal.status = RENEWAL_STATUS_RENEWED
        renewal.created_contract = new_contract
        renewal.save(update_fields=['status', 'created_contract', 'updated_at'])

        _add_event(renewal, role, name, confirm_action)
        _add_event(renewal, role, name, '生成新合同', f'已生成下一份合同 #{new_contract.id}，月租 ¥{new_contract.rent}')
        logger.info('续租#%s 成功，生成新合同 #%s', renewal.id, new_contract.id)
    return renewal


def start_renewal(contract_id, role, name, data):
    """租客从合同卡片发起续租：填写新租期与期望月租。"""
    if role != ROLE_TENANT:
        raise BusinessError('RENEWAL_FORBIDDEN', data={'expectedRole': ROLE_TENANT})
    contract = get_contract_or_404(contract_id)
    if name != contract.tenant_name:
        raise BusinessError('RENEWAL_FORBIDDEN')
    if contract.status != CONTRACT_STATUS_ACTIVE:
        raise BusinessError('RENEWAL_STATE_INVALID', data={'contractStatus': contract.status})
    if contract.renewals.filter(status__in=ACTIVE_RENEWAL_STATUSES).exists():
        raise BusinessError('RENEWAL_DUPLICATE')

    start = _parse_date(data.get('newStartDate'), 'newStartDate')
    end = _parse_date(data.get('newEndDate'), 'newEndDate')
    rent = _parse_rent(data.get('proposedRent'), 'proposedRent')
    if start >= end:
        raise BusinessError('RENEWAL_INVALID_INPUT', data={'field': 'newEndDate'})
    message = (data.get('message') or '').strip()[:200]

    renewal = RenewalRequest.objects.create(
        contract=contract,
        property=contract.property,
        tenant_name=contract.tenant_name,
        landlord_name=contract.landlord_name,
        new_start_date=start,
        new_end_date=end,
        proposed_rent=rent,
        current_rent=contract.rent,
        status=RENEWAL_STATUS_PENDING_LANDLORD,
        message=message,
    )
    _add_event(renewal, ROLE_TENANT, name, '发起续租', f'期望月租 ¥{rent}')
    logger.info('合同#%s 发起续租 #%s', contract.id, renewal.id)
    return renewal


def landlord_accept(renewal_id, role, name):
    renewal = get_renewal_or_404(renewal_id)
    _assert_not_finished(renewal)
    _assert_actor(renewal, role, name, ROLE_LANDLORD)
    if renewal.status != RENEWAL_STATUS_PENDING_LANDLORD:
        raise BusinessError('RENEWAL_STATE_INVALID', data={'status': renewal.status})
    # 房东直接接受同样要防止把同一套房答应给两个租客
    _ensure_no_conflict(renewal, role, name)
    _add_event(renewal, role, name, '房东接受', f'同意月租 ¥{renewal.proposed_rent}')
    return _complete_renewal(renewal, role, name, '房东接受')


def landlord_counter(renewal_id, role, name, data):
    """房东还价：改价后回到租客确认。"""
    renewal = get_renewal_or_404(renewal_id)
    _assert_not_finished(renewal)
    _assert_actor(renewal, role, name, ROLE_LANDLORD)
    if renewal.status != RENEWAL_STATUS_PENDING_LANDLORD:
        raise BusinessError('RENEWAL_STATE_INVALID', data={'status': renewal.status})
    rent = _parse_rent(data.get('proposedRent'), 'proposedRent')
    note = (data.get('note') or '').strip()[:200]

    renewal.proposed_rent = rent
    renewal.status = RENEWAL_STATUS_PENDING_TENANT
    renewal.save(update_fields=['proposed_rent', 'status', 'updated_at'])
    event_note = f'还价为 ¥{rent}' + (f'：{note}' if note else '')
    _add_event(renewal, role, name, '房东还价', event_note)
    logger.info('续租#%s 房东还价 ¥%s', renewal.id, rent)
    return renewal


def landlord_reject(renewal_id, role, name, data=None):
    renewal = get_renewal_or_404(renewal_id)
    _assert_not_finished(renewal)
    _assert_actor(renewal, role, name, ROLE_LANDLORD)
    if renewal.status != RENEWAL_STATUS_PENDING_LANDLORD:
        raise BusinessError('RENEWAL_STATE_INVALID', data={'status': renewal.status})
    note = ((data or {}).get('note') or '').strip()[:200]
    renewal.status = RENEWAL_STATUS_CANCELLED
    renewal.save(update_fields=['status', 'updated_at'])
    _add_event(renewal, role, name, '房东拒绝', note)
    logger.info('续租#%s 房东拒绝', renewal.id)
    return renewal


def tenant_confirm(renewal_id, role, name):
    """租客确认房东还价后的新租期与价格；冲突时说明冲突合同。"""
    renewal = get_renewal_or_404(renewal_id)
    _assert_not_finished(renewal)
    _assert_actor(renewal, role, name, ROLE_TENANT)
    if renewal.status != RENEWAL_STATUS_PENDING_TENANT:
        raise BusinessError('RENEWAL_STATE_INVALID', data={'status': renewal.status})
    _ensure_no_conflict(renewal, role, name)
    _add_event(renewal, role, name, '租客确认', f'确认月租 ¥{renewal.proposed_rent}')
    return _complete_renewal(renewal, role, name, '租客确认')


def tenant_cancel(renewal_id, role, name, data=None):
    renewal = get_renewal_or_404(renewal_id)
    _assert_not_finished(renewal)
    _assert_actor(renewal, role, name, ROLE_TENANT)
    note = ((data or {}).get('note') or '').strip()[:200]
    renewal.status = RENEWAL_STATUS_CANCELLED
    renewal.save(update_fields=['status', 'updated_at'])
    _add_event(renewal, role, name, '租客取消', note)
    logger.info('续租#%s 租客取消', renewal.id)
    return renewal
