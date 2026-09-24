from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import RenewalSerializer, TenantConfirmSerializer
from ..services import confirm_renewal


class RenewalConfirmView(APIView):
    """还价后由租客确认，或租客取消续租。"""

    def post(self, request, renewal_id):
        payload = TenantConfirmSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        renewal = confirm_renewal(
            renewal_id,
            {'action': payload.validated_data['action']},
            actor_role=request.data.get('role', '租客'),
        )
        return Response(RenewalSerializer(renewal).data)
