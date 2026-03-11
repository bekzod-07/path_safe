from django.contrib import admin
from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.contrib.auth.decorators import login_required
from django.views.generic import RedirectView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Viewlarni import qilish
from accounts.views import (
    RegisterView, 
    LoginView, 
    VerifyOTPView, 
    LocationAPIView,
    AppUsageAPIView
)

schema_view = get_schema_view(
   openapi.Info(
      title="Path Safe API",
      default_version='v1',
      description="Farzand xavfsizligi loyihasi uchun barcha API hujjatlari",
   ),
   public=False,
   permission_classes=(permissions.IsAuthenticated,),
)

urlpatterns = [
    path('', login_required(RedirectView.as_view(url='/swagger/'))),
    path('admin/', admin.site.urls),
    
    # Auth API
    path('register/', RegisterView.as_view(), name='register'),
    path('verify/', VerifyOTPView.as_view(), name='verify'),
    path('login/', LoginView.as_view(), name='login'),
    
    # Services API
    path('location/', LocationAPIView.as_view(), name='location'),
    path('app-usage/', AppUsageAPIView.as_view(), name='app_usage'),
    
    # Swagger
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]

# DEBUG=False bo'lganda statik va media fayllarni ko'rsatish
urlpatterns += [
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]