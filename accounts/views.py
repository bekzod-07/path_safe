import random
from datetime import timedelta

from django.utils import timezone
from django.contrib.auth import authenticate

from rest_framework import status, generics, permissions
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .models import User, UserLocation, AppUsage, FamilyRelation
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    VerifyOTPSerializer,
    UserSerializer,
    LocationSerializer,
    AppUsageSerializer,
    FamilyChildSerializer,
    FamilyUpsertSerializer,
    FamilyDeleteSerializer,
)

import random
from django.conf import settings

def generate_otp():
    if settings.DEBUG:
        return "123456"
    return str(random.randint(100000, 999999))


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        tags=["auth"],
        operation_summary="Ro‘yxatdan o‘tish",
        request_body=RegisterSerializer,
        responses={201: UserSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp_code = generate_otp()
        user = serializer.save(otp_code=otp_code, is_verified=False)

        print(f"\n[{timezone.now()}] >>> SMS YUBORILDI {user.phone}: {otp_code} <<<\n")

        return Response(
            {
                "message": "Foydalanuvchi yaratildi. OTP yuborildi.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        tags=["auth"],
        operation_summary="OTP kodni tasdiqlash",
        request_body=VerifyOTPSerializer,
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        code = serializer.validated_data["code"]

        user = User.objects.filter(phone=phone, otp_code=code).first()
        if not user:
            return Response(
                {"error": "Kod noto‘g‘ri yoki foydalanuvchi topilmadi"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_verified = True
        user.otp_code = None
        user.save(update_fields=["is_verified", "otp_code"])

        return Response(
            {"message": "Muvaffaqiyatli tasdiqlandi"},
            status=status.HTTP_200_OK,
        )


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        tags=["auth"],
        operation_summary="Tizimga kirish",
        request_body=LoginSerializer,
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"]
        password = serializer.validated_data["password"]

        user = authenticate(phone=phone, password=password)
        if not user:
            return Response(
                {"error": "Telefon yoki parol xato"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_verified:
            return Response(
                {"error": "Telefon raqam hali tasdiqlanmagan"},
                status=status.HTTP_403_FORBIDDEN,
            )

        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "token": token.key,
                "full_name": user.full_name,
                "phone": user.phone,
                "role": user.role,
            },
            status=status.HTTP_200_OK,
        )


class LocationAPIView(generics.ListCreateAPIView):
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        tags=["location"],
        manual_parameters=[
            openapi.Parameter("phone", openapi.IN_QUERY, description="Telefon raqam", type=openapi.TYPE_STRING),
            openapi.Parameter("period", openapi.IN_QUERY, description="Kunlar soni", type=openapi.TYPE_INTEGER),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        phone = self.request.query_params.get("phone")
        period = self.request.query_params.get("period")

        if user.role == User.ROLE_PARENT:
            queryset = UserLocation.objects.filter(
                user__parent_relation__parent=user
            ).select_related("user")
        else:
            queryset = UserLocation.objects.filter(user=user).select_related("user")

        if phone:
            queryset = queryset.filter(user__phone=phone)

        if period:
            try:
                days = int(period)
                start_date = timezone.now() - timedelta(days=days)
                queryset = queryset.filter(created_at__gte=start_date)
            except ValueError:
                pass

        return queryset.order_by("-created_at")

    @swagger_auto_schema(
        tags=["location"],
        operation_summary="Foydalanuvchining geolokatsiyasini saqlash",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["lat", "lng"],
            properties={
                "lat": openapi.Schema(type=openapi.TYPE_NUMBER, example=41.311081),
                "lng": openapi.Schema(type=openapi.TYPE_NUMBER, example=69.240562),
                "address": openapi.Schema(type=openapi.TYPE_STRING, example="Toshkent shahri"),
            },
        ),
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AppUsageAPIView(generics.ListCreateAPIView):
    serializer_class = AppUsageSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        tags=["app-usage"],
        manual_parameters=[
            openapi.Parameter("phone", openapi.IN_QUERY, description="Telefon raqam", type=openapi.TYPE_STRING),
            openapi.Parameter("period", openapi.IN_QUERY, description="Kunlar soni", type=openapi.TYPE_INTEGER),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        phone = self.request.query_params.get("phone")
        period = self.request.query_params.get("period")

        if user.role == User.ROLE_PARENT:
            queryset = AppUsage.objects.filter(
                user__parent_relation__parent=user
            ).select_related("user")
        else:
            queryset = AppUsage.objects.filter(user=user).select_related("user")

        if phone:
            queryset = queryset.filter(user__phone=phone)

        if period:
            try:
                days = int(period)
                start_date = timezone.now() - timedelta(days=days)
                queryset = queryset.filter(created_at__gte=start_date)
            except ValueError:
                pass

        return queryset.order_by("-created_at")

    @swagger_auto_schema(
        tags=["app-usage"],
        operation_summary="Ilova ishlatilish ma’lumotini saqlash",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["app_name", "usage_time"],
            properties={
                "app_name": openapi.Schema(type=openapi.TYPE_STRING, example="YouTube"),
                "usage_time": openapi.Schema(type=openapi.TYPE_INTEGER, example=25),
            },
        ),
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FamilyManagementView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _ensure_parent(self, request):
        if request.user.role != User.ROLE_PARENT:
            return Response(
                {"error": "Faqat ota-onalar family endpointdan foydalana oladi"},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None

    @swagger_auto_schema(
        tags=["family"],
        operation_summary="Login qilgan ota-onaga biriktirilgan farzandlar ro‘yxati",
        manual_parameters=[
            openapi.Parameter(
                "child_phone",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Muayyan farzandni raqami bo‘yicha qidirish",
            )
        ],
        responses={200: FamilyChildSerializer(many=True)},
    )
    def get(self, request):
        blocked = self._ensure_parent(request)
        if blocked:
            return blocked

        child_phone = request.query_params.get("child_phone")

        relations = FamilyRelation.objects.filter(parent=request.user).select_related("child")

        if child_phone:
            relations = relations.filter(child__phone=child_phone)

        serializer = FamilyChildSerializer(relations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=["family"],
        operation_summary="Farzandni ota-onaga biriktirish yoki labelni yangilash",
        request_body=FamilyUpsertSerializer,
    )
    def post(self, request):
        blocked = self._ensure_parent(request)
        if blocked:
            return blocked

        serializer = FamilyUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        child_phone = serializer.validated_data["child_phone"]
        child_label = serializer.validated_data["child_label"]

        child = User.objects.filter(phone=child_phone, role=User.ROLE_CHILD).first()
        if not child:
            return Response(
                {"error": "Bunday raqamli farzand topilmadi"},
                status=status.HTTP_404_NOT_FOUND,
            )

        relation, created = FamilyRelation.objects.update_or_create(
            parent=request.user,
            child=child,
            defaults={"child_label": child_label},
        )

        return Response(
            {
                "status": "success",
                "created": created,
                "message": (
                    f"{child.full_name} muvaffaqiyatli biriktirildi"
                    if created
                    else f"{child.full_name} uchun label yangilandi"
                ),
                "child": FamilyChildSerializer(relation).data,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        tags=["family"],
        operation_summary="Farzandni ota-onadan uzish",
        manual_parameters=[
            openapi.Parameter(
                "child_phone",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=False,
                description="Farzand telefon raqami",
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "child_phone": openapi.Schema(type=openapi.TYPE_STRING, example="+998901112233"),
            },
        ),
    )
    def delete(self, request):
        blocked = self._ensure_parent(request)
        if blocked:
            return blocked

        child_phone = request.query_params.get("child_phone") or request.data.get("child_phone")

        serializer = FamilyDeleteSerializer(data={"child_phone": child_phone})
        serializer.is_valid(raise_exception=True)

        relation = FamilyRelation.objects.filter(
            parent=request.user,
            child__phone=serializer.validated_data["child_phone"],
        ).first()

        if not relation:
            return Response(
                {"error": "Bunday birikma topilmadi"},
                status=status.HTTP_404_NOT_FOUND,
            )

        relation.delete()
        return Response(
            {"message": "Farzand muvaffaqiyatli olib tashlandi"},
            status=status.HTTP_200_OK,
        )