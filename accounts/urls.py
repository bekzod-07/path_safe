from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import RedirectView
from .views import (
    RegisterView, 
    VerifyOTPView, 
    LoginView, 
    LocationAPIView, 
    AppUsageAPIView
)

urlpatterns = [
    # Bosh sahifaga kirganda (api.kyotosushi.uz/) avval login so'raydi, 
    # keyin Swaggerga yuboradi. Agar login qilmagan bo'lsa, /login/ sahifasiga o'tadi.
    path('', login_required(RedirectView.as_view(url='/swagger/'))),

    # Ro'yxatdan o'tish va Tasdiqlash (Bular IsAuthenticated'dan mustasno bo'lishi kerak)
    path('register/', RegisterView.as_view(), name='register'),
    path('verify/', VerifyOTPView.as_view(), name='verify'),
    path('login/', LoginView.as_view(), name='login'),

    # Xavfsiz endpointlar (Faqat login qilganlar uchun)
    path('location/', LocationAPIView.as_view(), name='location'),
    path('app-usage/', AppUsageAPIView.as_view(), name='app_usage'),
]