from django.db import models

from app.constants.enums import (
    CONTRACT_STATUS_ACTIVE,
    CONTRACT_STATUSES,
    RENEWAL_STATUS_PENDING_LANDLORD,
    RENEWAL_STATUSES,
    ROLE_LANDLORD,
    ROLE_TENANT,
)

ROLE_CHOICES = ((ROLE_TENANT, ROLE_TENANT), (ROLE_LANDLORD, ROLE_LANDLORD))


class Contract(models.Model):
    """租赁合同；续租成功后原合同标记为已续租并指向新生成的下一份合同。"""

    property = models.ForeignKey('properties.Property', on_delete=models.PROTECT, related_name='contracts')
    tenant_name = models.CharField('租客', max_length=40)
    landlord_name = models.CharField('房东', max_length=40)
    rent = models.PositiveIntegerField('月租（元）')
    deposit = models.PositiveIntegerField('押金（元）', default=0)
    start_date = models.DateField('租期开始')
    end_date = models.DateField('租期结束')
    status = models.CharField('状态', max_length=12, choices=[(s, s) for s in CONTRACT_STATUSES], default=CONTRACT_STATUS_ACTIVE)
    renewed_contract = models.ForeignKey(
        'self', on_delete=models.PROTECT, null=True, blank=True, related_name='previous_contract',
        verbose_name='续租生成的新合同',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '合同'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']


class RenewalRequest(models.Model):
    """从合同卡片发起的续租协商。"""

    contract = models.ForeignKey(Contract, on_delete=models.PROTECT, related_name='renewals', verbose_name='原合同')
    property = models.ForeignKey('properties.Property', on_delete=models.PROTECT, related_name='renewals', verbose_name='房源')
    tenant_name = models.CharField('租客', max_length=40)
    landlord_name = models.CharField('房东', max_length=40)
    new_start_date = models.DateField('新租期开始')
    new_end_date = models.DateField('新租期结束')
    proposed_rent = models.PositiveIntegerField('期望月租（元）')
    current_rent = models.PositiveIntegerField('发起时月租（元）')
    status = models.CharField(
        '状态', max_length=12,
        choices=[(s, s) for s in RENEWAL_STATUSES],
        default=RENEWAL_STATUS_PENDING_LANDLORD,
    )
    message = models.CharField('附言', max_length=200, blank=True, default='')
    created_contract = models.ForeignKey(
        Contract, on_delete=models.PROTECT, null=True, blank=True, related_name='from_renewal',
        verbose_name='续租成功后生成的新合同',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '续租协商'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']


class RenewalEvent(models.Model):
    """续租协商处理流水：每次处理都留下角色和时间。"""

    renewal = models.ForeignKey(RenewalRequest, on_delete=models.CASCADE, related_name='events')
    actor_role = models.CharField('处理人角色', max_length=12, choices=ROLE_CHOICES)
    actor_name = models.CharField('处理人', max_length=40)
    action = models.CharField('动作', max_length=20)
    note = models.CharField('说明', max_length=200, blank=True, default='')
    created_at = models.DateTimeField('处理时间', auto_now_add=True)

    class Meta:
        verbose_name = '续租处理记录'
        verbose_name_plural = verbose_name
        ordering = ['created_at']
