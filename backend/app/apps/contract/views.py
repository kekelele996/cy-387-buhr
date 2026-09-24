from rest_framework.response import Response
from rest_framework.views import APIView

from app.apps.contract import services
from app.apps.contract.actors import get_actor
from app.apps.contract.models import Contract, RenewalRequest
from app.apps.contract.serializers import ContractSerializer, RenewalRequestSerializer


def _serialize_renewal(renewal):
    return RenewalRequestSerializer(renewal).data


class ContractListView(APIView):
    """合同卡片列表：按当前角色只返回与自己相关的合同。"""

    def get(self, request):
        role, name = get_actor(request)
        role_field = 'tenant_name' if role == '租客' else 'landlord_name'
        contracts = Contract.objects.select_related('property').filter(**{role_field: name})
        return Response(ContractSerializer(contracts, many=True).data)


class RenewalListCreateView(APIView):
    def get(self, request):
        get_actor(request)
        renewals = RenewalRequest.objects.select_related('contract', 'property').prefetch_related('events')
        return Response([_serialize_renewal(item) for item in renewals])

    def post(self, request):
        role, name = get_actor(request)
        contract_id = request.data.get('contractId')
        renewal = services.start_renewal(contract_id, role, name, request.data)
        return Response(_serialize_renewal(renewal), status=201)


class RenewalAcceptView(APIView):
    def post(self, request, renewal_id):
        role, name = get_actor(request)
        renewal = services.landlord_accept(renewal_id, role, name)
        return Response(_serialize_renewal(renewal))


class RenewalCounterView(APIView):
    def post(self, request, renewal_id):
        role, name = get_actor(request)
        renewal = services.landlord_counter(renewal_id, role, name, request.data)
        return Response(_serialize_renewal(renewal))


class RenewalRejectView(APIView):
    def post(self, request, renewal_id):
        role, name = get_actor(request)
        renewal = services.landlord_reject(renewal_id, role, name, request.data)
        return Response(_serialize_renewal(renewal))


class RenewalConfirmView(APIView):
    def post(self, request, renewal_id):
        role, name = get_actor(request)
        renewal = services.tenant_confirm(renewal_id, role, name)
        return Response(_serialize_renewal(renewal))


class RenewalCancelView(APIView):
    def post(self, request, renewal_id):
        role, name = get_actor(request)
        if role == '房东':
            renewal = services.landlord_reject(renewal_id, role, name, request.data)
        else:
            renewal = services.tenant_cancel(renewal_id, role, name, request.data)
        return Response(_serialize_renewal(renewal))
