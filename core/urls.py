from django.contrib import admin
from django.urls import path, re_path
from django.conf import settings
from django.views.static import serve
from django.contrib.auth.decorators import login_required
from django.views.generic import RedirectView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from accounts.views import (
    RegisterView,
    LoginView,
    VerifyOTPView,
    UserProfileAPIView,
    LocationAPIView,
    AppUsageAPIView,
    FamilyManagementView,
    FamilyVerifyView,   # <-- shu qo‘shiladi
)

schema_view = get_schema_view(
    openapi.Info(
        title="Path Safe API",
        default_version="v1",
        description="Farzand xavfsizligi loyihasi uchun barcha API hujjatlari",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("", login_required(RedirectView.as_view(url="/swagger/"))),
    path("admin/", admin.site.urls),

    path("register/", RegisterView.as_view(), name="register"),
    path("verify/", VerifyOTPView.as_view(), name="verify"),
    path("login/", LoginView.as_view(), name="login"),

    path("profile/", UserProfileAPIView.as_view(), name="profile"),
    path("location/", LocationAPIView.as_view(), name="location"),
    path("app-usage/", AppUsageAPIView.as_view(), name="app_usage"),

    path("family/", FamilyManagementView.as_view(), name="family_management"),
    path("family/verify/", FamilyVerifyView.as_view(), name="family_verify"),  # <-- shu qo‘shiladi

    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
]

urlpatterns += [
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]