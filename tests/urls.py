from django.urls import path
from rest_framework.response import Response
from rest_framework.views import APIView


class PingView(APIView):
    def get(self, request):
        return Response({"ok": True})


urlpatterns = [path("ping/", PingView.as_view(), name="ping")]
