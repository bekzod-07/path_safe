from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import RedirectView
from .views import (
    RegisterView, 
    VerifyOTPView, 
    LoginView, 
    LocationAPIView, 
    AppUsageAPIView,
    FamilyManagementView
)

urlpatterns = [
    # Bosh sahifa - Swaggerga yo'naltirish
    # Eslatma: login_required ishlashi uchun settings.py da LOGIN_URL sozlangan bo'lishi kerak
    path('', login_required(RedirectView.as_view(url='/swagger/'))),

    # Ochiq endpointlar (Public)
    path('register/', RegisterView.as_view(), name='register'),
    path('verify/', VerifyOTPView.as_view(), name='verify'),
    path('login/', LoginView.as_view(), name='login'),

    # Yopiq endpointlar (Private - Token talab qilinadi)
    path('location/', LocationAPIView.as_view(), name='location'),
    path('app-usage/', AppUsageAPIView.as_view(), name='app_usage'),
    path('family/', FamilyManagementView.as_view(), name='family_management'),
]