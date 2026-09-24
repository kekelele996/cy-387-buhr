from rest_framework import serializers

from app.apps.contract.models import Contract, RenewalEvent, RenewalRequest


class RenewalEventSerializer(serializers.ModelSerializer):
    actorRole = serializers.CharField(source='actor_role')
    actorName = serializers.CharField(source='actor_name')
    time = serializers.SerializerMethodField()

    class Meta:
        model = RenewalEvent
        fields = ['id', 'actorRole', 'actorName', 'action', 'note', 'time']

    def get_time(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')


class RenewalRequestSerializer(serializers.ModelSerializer):
    contractId = serializers.IntegerField(source='contract_id')
    propertyId = serializers.IntegerField(source='property_id')
    tenantName = serializers.CharField(source='tenant_name')
    landlordName = serializers.CharField(source='landlord_name')
    newStartDate = serializers.DateField(source='new_start_date', format='%Y-%m-%d')
    newEndDate = serializers.DateField(source='new_end_date', format='%Y-%m-%d')
    proposedRent = serializers.IntegerField(source='proposed_rent')
    currentRent = serializers.IntegerField(source='current_rent')
    createdContractId = serializers.SerializerMethodField()
    events = RenewalEventSerializer(many=True, read_only=True)
    createdAt = serializers.SerializerMethodField()
    updatedAt = serializers.SerializerMethodField()

    class Meta:
        model = RenewalRequest
        fields = [
            'id', 'contractId', 'propertyId', 'tenantName', 'landlordName',
            'newStartDate', 'newEndDate', 'proposedRent', 'currentRent',
            'status', 'message', 'createdContractId', 'events',
            'createdAt', 'updatedAt',
        ]

    def get_createdContractId(self, obj):
        return obj.created_contract_id

    def get_createdAt(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')

    def get_updatedAt(self, obj):
        return obj.updated_at.strftime('%Y-%m-%d %H:%M')


class ContractSerializer(serializers.ModelSerializer):
    propertyId = serializers.IntegerField(source='property_id')
    community = serializers.CharField(source='property.community', read_only=True)
    layout = serializers.CharField(source='property.layout', read_only=True)
    tenantName = serializers.CharField(source='tenant_name')
    landlordName = serializers.CharField(source='landlord_name')
    startDate = serializers.DateField(source='start_date', format='%Y-%m-%d')
    endDate = serializers.DateField(source='end_date', format='%Y-%m-%d')
    renewedContractId = serializers.SerializerMethodField()
    renewal = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = [
            'id', 'propertyId', 'community', 'layout',
            'tenantName', 'landlordName', 'rent', 'deposit',
            'startDate', 'endDate', 'status',
            'renewedContractId', 'renewal',
        ]

    def get_renewedContractId(self, obj):
        return obj.renewed_contract_id

    def get_renewal(self, obj):
        renewal = obj.renewals.order_by('-created_at').first()
        if renewal is None:
            return None
        return RenewalRequestSerializer(renewal).data
