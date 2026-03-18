from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import RedirectView

from .views import (
    RegisterView,
    VerifyOTPView,
    LoginView,
    UserProfileAPIView,
    LocationAPIView,
    AppUsageAPIView,
    FamilyManagementView,
    FamilyVerifyView,
)

urlpatterns = [
    path("", login_required(RedirectView.as_view(url="/swagger/"))),
    path("register/", RegisterView.as_view(), name="register"),
    path("verify/", VerifyOTPView.as_view(), name="verify"),
    path("login/", LoginView.as_view(), name="login"),
    path("profile/", UserProfileAPIView.as_view(), name="profile"),
    path("location/", LocationAPIView.as_view(), name="location"),
    path("app-usage/", AppUsageAPIView.as_view(), name="app_usage"),
    path("family/", FamilyManagementView.as_view(), name="family_management"),
    path("family/verify/", FamilyVerifyView.as_view(), name="family-verify"),

]
