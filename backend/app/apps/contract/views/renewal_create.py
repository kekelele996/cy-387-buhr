from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import RenewalCreateSerializer, RenewalSerializer
from ..services import create_renewal


class RenewalCreateView(APIView):
    """租客从合同卡片发起续租。"""

    def post(self, request, contract_id):
        payload = RenewalCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        renewal = create_renewal(
            contract_id, payload.validated_data, actor_role=request.data.get('role', '租客')
        )
        return Response(RenewalSerializer(renewal).data, status=201)
