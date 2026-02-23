from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import WAbits
from .serializers import WAbitsSerializers
from .default_flow import DEFAULT_FLOW_JSON


@api_view(['GET', 'POST'])
def flow_json_view(request):
    if request.method == 'POST':
        tenant_id = request.headers.get('X-Tenant-Id')

        if not tenant_id:
            return Response({"error": "Missing X-Tenant-Id in headers"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # request.data is already parsed JSON
            flow = WAbits.objects.create(
                tenant_id=tenant_id,
                flow_json=request.data
            )
            return Response({"message": "Flow saved successfully", "id": flow.id}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


    elif request.method == 'GET':
        tenant_id = request.headers.get('X-Tenant-Id')
        if not tenant_id:
            return Response({'error': 'Missing tenant_id'}, status=status.HTTP_400_BAD_REQUEST)

        flows = WAbits.objects.filter(tenant_id=tenant_id)
        serializer = WAbitsSerializers(flows, many=True)

        combined_flows = [item['flow_json'] for item in serializer.data] + DEFAULT_FLOW_JSON

        return Response(combined_flows, status=status.HTTP_200_OK)
