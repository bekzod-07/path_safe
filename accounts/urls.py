from django.urls import path
from .views import RegisterView, VerifyOTPView, LoginView, LocationAPIView, AppUsageAPIView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify/', VerifyOTPView.as_view(), name='verify'),
    path('login/', LoginView.as_view(), name='login'),
    path('location/', LocationAPIView.as_view(), name='location'),
    path('app-usage/', AppUsageAPIView.as_view(), name='app_usage'),
]