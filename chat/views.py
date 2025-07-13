from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Message, MessageThread
from .serializers import MessageSerializer

class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        file = request.data.get("file")
        thread_id = request.data.get("thread_id")

        message = Message.objects.create(
            sender=request.user,
            thread_id=thread_id,
            type="file",
            file=file
        )

        return Response(MessageSerializer(message).data)
