from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Contract
from ..serializers import ContractSerializer


class ContractListView(APIView):
    """合同卡片列表，每张卡片附带最近一次续租协商状态。"""

    def get(self, request):
        contracts = (
            Contract.objects.select_related('property')
            .prefetch_related('renewals__events')
            .all()
        )
        return Response(ContractSerializer(contracts, many=True).data)
