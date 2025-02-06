from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookViewSet, ChatbotView

router = DefaultRouter()
router.register(r'books', BookViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/chatbot/', ChatbotView.as_view(), name='chatbot'),
]
