from rest_framework import serializers

from .models import Contract, Renewal, RenewalEvent


class RenewalEventSerializer(serializers.ModelSerializer):
    """续租处理留痕：角色 + 动作 + 时间。"""

    actorRole = serializers.CharField(source='actor_role', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', format='%Y-%m-%d %H:%M', read_only=True)

    class Meta:
        model = RenewalEvent
        fields = ['id', 'actorRole', 'action', 'rent', 'note', 'createdAt']


class RenewalSerializer(serializers.ModelSerializer):
    events = RenewalEventSerializer(many=True, read_only=True)
    startDate = serializers.DateField(source='start_date', read_only=True)
    endDate = serializers.DateField(source='end_date', read_only=True)
    expectedRent = serializers.IntegerField(source='expected_rent', read_only=True)
    newContractId = serializers.IntegerField(source='new_contract_id', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', format='%Y-%m-%d %H:%M', read_only=True)

    class Meta:
        model = Renewal
        fields = [
            'id', 'startDate', 'endDate', 'rent', 'expectedRent', 'status',
            'newContractId', 'createdAt', 'events',
        ]


class ContractSerializer(serializers.ModelSerializer):
    propertyId = serializers.IntegerField(source='property_id', read_only=True)
    community = serializers.CharField(source='property.community', read_only=True)
    tenantName = serializers.CharField(source='tenant_name', read_only=True)
    landlordName = serializers.CharField(source='landlord_name', read_only=True)
    startDate = serializers.DateField(source='start_date', read_only=True)
    endDate = serializers.DateField(source='end_date', read_only=True)
    renewedFromId = serializers.IntegerField(source='renewed_from_id', read_only=True)
    renewal = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = [
            'id', 'propertyId', 'community', 'tenantName', 'landlordName',
            'rent', 'startDate', 'endDate', 'status', 'renewedFromId', 'renewal',
        ]

    def get_renewal(self, obj):
        renewal = obj.renewals.order_by('-created_at').first()
        return RenewalSerializer(renewal).data if renewal else None


class RenewalCreateSerializer(serializers.Serializer):
    """租客发起续租：新租期 + 期望月租。"""

    startDate = serializers.DateField()
    endDate = serializers.DateField()
    expectedRent = serializers.IntegerField(min_value=1)


class LandlordRespondSerializer(serializers.Serializer):
    """房东接受 / 还价 / 拒绝。"""

    action = serializers.ChoiceField(choices=['accept', 'counter', 'reject'])
    rent = serializers.IntegerField(min_value=1, required=False)


class TenantConfirmSerializer(serializers.Serializer):
    """租客确认接受还价 / 取消续租。"""

    action = serializers.ChoiceField(choices=['confirm', 'cancel'])
