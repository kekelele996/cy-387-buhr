from django.db import models

from app.constants.enums import (
    CONTRACT_STATUS_ACTIVE,
    RENEWAL_ACTION_CREATE,
    RENEWAL_STATUS_PENDING_LANDLORD,
)


class Contract(models.Model):
    """租赁合同。"""

    property = models.ForeignKey(
        'properties.Property', related_name='contracts', on_delete=models.CASCADE
    )
    tenant_name = models.CharField(max_length=40, verbose_name='租客姓名')
    landlord_name = models.CharField(max_length=40, verbose_name='房东姓名')
    rent = models.IntegerField(verbose_name='月租（元）')
    start_date = models.DateField(verbose_name='租期开始')
    end_date = models.DateField(verbose_name='租期结束')
    status = models.CharField(max_length=20, default=CONTRACT_STATUS_ACTIVE, verbose_name='合同状态')
    # 续租成功后，由哪一份合同续租而来
    renewed_from = models.ForeignKey(
        'self', related_name='renewed_contracts', null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class Renewal(models.Model):
    """续租协商：租客发起，房东接受/还价/拒绝，还价后由租客确认。"""

    contract = models.ForeignKey(Contract, related_name='renewals', on_delete=models.CASCADE)
    start_date = models.DateField(verbose_name='期望新租期开始')
    end_date = models.DateField(verbose_name='期望新租期结束')
    rent = models.IntegerField(verbose_name='当前协商月租（元）')
    expected_rent = models.IntegerField(verbose_name='租客发起时的期望月租（元）')
    status = models.CharField(
        max_length=20,
        default=RENEWAL_STATUS_PENDING_LANDLORD,
        verbose_name='协商状态',
    )
    new_contract = models.ForeignKey(
        Contract, related_name='renewal_sources', null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class RenewalEvent(models.Model):
    """续租协商处理留痕：记录处理角色、动作和时间。"""

    renewal = models.ForeignKey(Renewal, related_name='events', on_delete=models.CASCADE)
    actor_role = models.CharField(max_length=20, verbose_name='处理角色')
    action = models.CharField(max_length=20, default=RENEWAL_ACTION_CREATE, verbose_name='处理动作')
    rent = models.IntegerField(null=True, blank=True, verbose_name='本次处理涉及的月租')
    note = models.CharField(max_length=200, blank=True, default='', verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
