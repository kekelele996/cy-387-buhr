from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import LandlordRespondSerializer, RenewalSerializer
from ..services import respond_renewal


class RenewalRespondView(APIView):
    """房东接受、还价或拒绝续租申请。"""

    def post(self, request, renewal_id):
        payload = LandlordRespondSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        renewal = respond_renewal(
            renewal_id,
            {
                'action': payload.validated_data['action'],
                'rent': payload.validated_data.get('rent'),
            },
            actor_role=request.data.get('role', '房东'),
        )
        return Response(RenewalSerializer(renewal).data)
