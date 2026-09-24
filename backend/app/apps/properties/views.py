from rest_framework.response import Response
from rest_framework.views import APIView

from app.apps.properties.models import Property
from app.apps.properties.serializers import PropertySerializer


class PropertyListView(APIView):
    def get(self, request):
        properties = Property.objects.all()
        return Response(PropertySerializer(properties, many=True).data)
