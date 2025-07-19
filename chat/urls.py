from rest_framework.routers import DefaultRouter
from .views import ChatViewSet, MessageViewSet
from django.urls import path, include

router = DefaultRouter()
router.register('chats', ChatViewSet)
router.register('messages', MessageViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
