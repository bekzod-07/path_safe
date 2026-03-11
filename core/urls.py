from django.contrib import admin
from django.urls import path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Viewlarni import qilish (HAMMASINI - AppUsage qo'shildi)
from accounts.views import (
    RegisterView, 
    LoginView, 
    VerifyOTPView, 
    LocationAPIView,
    AppUsageAPIView  # <--- Shuni qo'shish esdan chiqqan
)

schema_view = get_schema_view(
   openapi.Info(
      title="Path Safe API",
      default_version='v1',
      description="Farzand xavfsizligi loyihasi uchun barcha API hujjatlari",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth API qismi
    path('register/', RegisterView.as_view(), name='register'),
    path('verify/', VerifyOTPView.as_view(), name='verify'),
    path('login/', LoginView.as_view(), name='login'),
    
    # Location (Geolokatsiya) API qismi
    path('location/', LocationAPIView.as_view(), name='location'),

    # App Usage (Ilova nazorati) API qismi
    path('app-usage/', AppUsageAPIView.as_view(), name='app_usage'),
    
    # Swagger (Hujjatlashtirish)
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]