from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Property
from .serializers import PropertySerializer


class PropertyListView(APIView):
    def get(self, request):
        properties = Property.objects.all()
        return Response(PropertySerializer(properties, many=True).data)
