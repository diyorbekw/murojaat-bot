"""
API URLs
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from . import views

router = DefaultRouter()
router.register(r'users', views.TelegramUserViewSet)
router.register(r'mahallas', views.MahallaViewSet)
router.register(r'categories', views.CategoryViewSet)
router.register(r'complaints', views.ComplaintViewSet)
router.register(r'history', views.StatusHistoryViewSet, basename='history')
router.register(r'notifications', views.NotificationViewSet, basename='notification')  # basename qo'shildi

schema_view = get_schema_view(
    openapi.Info(
        title="Murojaatlar Tizimi API",
        default_version='v1',
        description="Telegram murojaatlar tizimi API",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="admin@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
    
    # Public endpoints for Telegram bot
    path('telegram/register/', views.telegram_register_user, name='telegram-register'),
    path('telegram/mahallas/', views.get_mahallas, name='telegram-mahallas'),
    path('telegram/categories/', views.get_categories, name='telegram-categories'),
    path('telegram/webhook/', views.telegram_webhook, name='telegram-webhook'),
    
    # Statistics
    path('stats/', views.StatsAPIView.as_view(), name='stats'),
    
    # Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]