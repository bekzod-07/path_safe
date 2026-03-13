import random
from datetime import timedelta

from django.contrib.auth import authenticate
from django.db.models import Q
from django.utils import timezone

from rest_framework import generics, permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .models import (
    User,
    UserLocation,
    AppUsage,
    FamilyRelation,
    FamilyLinkRequest,
)

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    VerifyOTPSerializer,
    UserSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    LocationSerializer,
    AppUsageSerializer,
    FamilyChildSerializer,
    FamilyRequestSerializer,
    FamilyVerifySerializer,
    FamilyUpdateSerializer,
    FamilyDeleteSerializer,
)


TEST_OTP_CODE = "123456"
ALLOW_TEST_OTP_FOR_ALL_USERS = True
FAMILY_OTP_EXPIRE_MINUTES = 5


def generate_otp():
    if ALLOW_TEST_OTP_FOR_ALL_USERS:
        return TEST_OTP_CODE
    return str(random.randint(100000, 999999))


def normalize_name(value: str) -> str:
    return " ".join(value.strip().lower().split())


def can_access_target_user(actor, target_user):
    if actor == target_user:
        return True

    if actor.role == User.ROLE_PARENT:
        return FamilyRelation.objects.filter(parent=actor, child=target_user).exists()

    return False


def send_test_sms(phone: str, code: str, reason: str = "OTP"):
    print(f"\n[{timezone.now()}] >>> {reason} SMS YUBORILDI {phone}: {code} <<<\n")


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

        send_test_sms(user.phone, otp_code, reason="REGISTER OTP")

        return Response(
            {
                "message": "Foydalanuvchi yaratildi. OTP yuborildi.",
                "otp_test_code": otp_code if ALLOW_TEST_OTP_FOR_ALL_USERS else None,
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

        phone = serializer.validated_data["phone"].strip()
        code = serializer.validated_data["code"].strip()

        user = User.objects.filter(phone=phone).first()
        if not user:
            return Response(
                {"error": "Foydalanuvchi topilmadi"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if ALLOW_TEST_OTP_FOR_ALL_USERS and code == TEST_OTP_CODE:
            user.is_verified = True
            user.otp_code = None
            user.save(update_fields=["is_verified", "otp_code"])
            return Response(
                {"message": "Muvaffaqiyatli tasdiqlandi"},
                status=status.HTTP_200_OK,
            )

        if user.otp_code != code:
            return Response(
                {"error": "Kod noto‘g‘ri"},
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

        phone = serializer.validated_data["phone"].strip()
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


class UserProfileAPIView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return UserProfileUpdateSerializer
        return UserProfileSerializer

    @swagger_auto_schema(
        tags=["auth"],
        operation_summary="Login qilgan foydalanuvchi profilini olish",
        responses={200: UserProfileSerializer},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=["auth"],
        operation_summary="Profilni qisman yangilash",
        request_body=UserProfileUpdateSerializer,
        responses={200: UserProfileSerializer},
    )
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=["auth"],
        operation_summary="Profilni to‘liq yangilash",
        request_body=UserProfileUpdateSerializer,
        responses={200: UserProfileSerializer},
    )
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        old_phone = instance.phone
        user = serializer.save()
        phone_changed = old_phone != user.phone

        response_data = {
            "message": "Profil muvaffaqiyatli yangilandi",
            "user": UserProfileSerializer(user).data,
        }

        if phone_changed:
            otp_code = generate_otp()
            user.is_verified = False
            user.otp_code = otp_code
            user.save(update_fields=["is_verified", "otp_code"])

            Token.objects.filter(user=user).delete()
            send_test_sms(user.phone, otp_code, reason="PROFILE PHONE CHANGE OTP")

            response_data.update(
                {
                    "message": "Telefon raqam o‘zgardi. Qayta OTP tasdiqlash kerak.",
                    "requires_reverification": True,
                    "otp_test_code": otp_code if ALLOW_TEST_OTP_FOR_ALL_USERS else None,
                    "user": UserProfileSerializer(user).data,
                }
            )

        return Response(response_data, status=status.HTTP_200_OK)


class LocationAPIView(generics.ListCreateAPIView):
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        tags=["location"],
        manual_parameters=[
            openapi.Parameter(
                "phone",
                openapi.IN_QUERY,
                description="Telefon raqam",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "period",
                openapi.IN_QUERY,
                description="Kunlar soni",
                type=openapi.TYPE_INTEGER,
            ),
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
                Q(user=user) | Q(user__parent_relation__parent=user)
            ).select_related("user").distinct()
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
        operation_summary="Telefon raqami orqali geolokatsiyani saqlash",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["phone", "lat", "lng"],
            properties={
                "phone": openapi.Schema(type=openapi.TYPE_STRING, example="+998901112233"),
                "lat": openapi.Schema(type=openapi.TYPE_NUMBER, example=41.311081),
                "lng": openapi.Schema(type=openapi.TYPE_NUMBER, example=69.240562),
                "address": openapi.Schema(type=openapi.TYPE_STRING, example="Toshkent shahri"),
            },
        ),
        responses={201: LocationSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"].strip()
        target_user = User.objects.filter(phone=phone).first()

        if not target_user:
            return Response(
                {"error": "Bunday telefon raqamli foydalanuvchi topilmadi"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not can_access_target_user(request.user, target_user):
            return Response(
                {"error": "Siz bu foydalanuvchi uchun lokatsiya yubora olmaysiz"},
                status=status.HTTP_403_FORBIDDEN,
            )

        location = UserLocation.objects.create(
            user=target_user,
            lat=serializer.validated_data["lat"],
            lng=serializer.validated_data["lng"],
            address=serializer.validated_data.get("address"),
        )

        return Response(
            self.get_serializer(location).data,
            status=status.HTTP_201_CREATED,
        )


class AppUsageAPIView(generics.ListCreateAPIView):
    serializer_class = AppUsageSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        tags=["app-usage"],
        manual_parameters=[
            openapi.Parameter(
                "phone",
                openapi.IN_QUERY,
                description="Telefon raqam",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "period",
                openapi.IN_QUERY,
                description="Kunlar soni",
                type=openapi.TYPE_INTEGER,
            ),
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
                Q(user=user) | Q(user__parent_relation__parent=user)
            ).select_related("user").distinct()
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
        operation_summary="Telefon raqami orqali app usage saqlash",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["phone", "app_name", "usage_time"],
            properties={
                "phone": openapi.Schema(type=openapi.TYPE_STRING, example="+998901112233"),
                "app_name": openapi.Schema(type=openapi.TYPE_STRING, example="YouTube"),
                "usage_time": openapi.Schema(type=openapi.TYPE_INTEGER, example=25),
            },
        ),
        responses={201: AppUsageSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data["phone"].strip()
        app_name = serializer.validated_data["app_name"].strip()
        usage_time = serializer.validated_data["usage_time"]

        target_user = User.objects.filter(phone=phone).first()
        if not target_user:
            return Response(
                {"error": "Foydalanuvchi topilmadi"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not can_access_target_user(request.user, target_user):
            return Response(
                {"error": "Siz bu foydalanuvchi uchun app usage yubora olmaysiz"},
                status=status.HTTP_403_FORBIDDEN,
            )

        app_usage, created = AppUsage.objects.update_or_create(
            user=target_user,
            app_name=app_name,
            defaults={"usage_time": usage_time},
        )

        return Response(
            {
                "created": created,
                "data": self.get_serializer(app_usage).data,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


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
        operation_summary="Farzandni biriktirish uchun OTP yuborish",
        request_body=FamilyRequestSerializer,
    )
    def post(self, request):
        blocked = self._ensure_parent(request)
        if blocked:
            return blocked

        serializer = FamilyRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        child_phone = serializer.validated_data["child_phone"]
        child_name = serializer.validated_data["child_name"]
        child_label = serializer.validated_data["child_label"]

        child = User.objects.filter(phone=child_phone, role=User.ROLE_CHILD).first()
        if not child:
            return Response(
                {"error": "Bunday telefon raqamli child topilmadi"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not child.is_verified:
            return Response(
                {"error": "Bu child akkaunt hali tasdiqlanmagan"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if normalize_name(child.full_name) != normalize_name(child_name):
            return Response(
                {"error": "Farzand ismi mos kelmadi"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if FamilyRelation.objects.filter(parent=request.user, child=child).exists():
            return Response(
                {"error": "Bu farzand allaqachon biriktirilgan"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp_code = generate_otp()
        expires_at = timezone.now() + timedelta(minutes=FAMILY_OTP_EXPIRE_MINUTES)

        FamilyLinkRequest.objects.filter(
            parent=request.user,
            child=child,
            is_used=False,
        ).update(is_used=True)

        FamilyLinkRequest.objects.create(
            parent=request.user,
            child=child,
            child_label=child_label,
            otp_code=otp_code,
            expires_at=expires_at,
            is_used=False,
        )

        send_test_sms(child.phone, otp_code, reason="FAMILY LINK OTP")

        return Response(
            {
                "status": "success",
                "message": "Tasdiqlash kodi yuborildi. Endi /family/verify/ orqali kodni tasdiqlang.",
                "child_phone": child.phone,
                "child_name": child.full_name,
                "otp_test_code": otp_code if ALLOW_TEST_OTP_FOR_ALL_USERS else None,
                "expires_in_minutes": FAMILY_OTP_EXPIRE_MINUTES,
            },
            status=status.HTTP_200_OK,
        )

    @swagger_auto_schema(
        tags=["family"],
        operation_summary="Biriktirilgan farzand labelini tahrirlash",
        request_body=FamilyUpdateSerializer,
        responses={200: FamilyChildSerializer},
    )
    def patch(self, request):
        blocked = self._ensure_parent(request)
        if blocked:
            return blocked

        serializer = FamilyUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        child_phone = serializer.validated_data["child_phone"]
        child_label = serializer.validated_data["child_label"]

        relation = FamilyRelation.objects.filter(
            parent=request.user,
            child__phone=child_phone,
        ).select_related("child").first()

        if not relation:
            return Response(
                {"error": "Tahrirlash uchun bunday family bog‘lanish topilmadi"},
                status=status.HTTP_404_NOT_FOUND,
            )

        relation.child_label = child_label
        relation.save(update_fields=["child_label"])

        return Response(
            {
                "status": "success",
                "updated": True,
                "message": f"{relation.child.full_name} uchun label yangilandi",
                "child": FamilyChildSerializer(relation).data,
            },
            status=status.HTTP_200_OK,
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
                "child_phone": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    example="+998901112233",
                ),
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


class FamilyVerifyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _ensure_parent(self, request):
        if request.user.role != User.ROLE_PARENT:
            return Response(
                {"error": "Faqat ota-onalar family verify endpointdan foydalana oladi"},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None

    @swagger_auto_schema(
        tags=["family"],
        operation_summary="Family biriktirish uchun OTP kodni tasdiqlash",
        request_body=FamilyVerifySerializer,
    )
    def post(self, request):
        blocked = self._ensure_parent(request)
        if blocked:
            return blocked

        serializer = FamilyVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        child_phone = serializer.validated_data["child_phone"]
        code = serializer.validated_data["code"].strip()

        child = User.objects.filter(phone=child_phone, role=User.ROLE_CHILD).first()
        if not child:
            return Response(
                {"error": "Bunday child topilmadi"},
                status=status.HTTP_404_NOT_FOUND,
            )

        link_request = FamilyLinkRequest.objects.filter(
            parent=request.user,
            child=child,
            is_used=False,
        ).order_by("-created_at").first()

        if not link_request:
            return Response(
                {"error": "Tasdiqlash uchun faol so‘rov topilmadi"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if link_request.expires_at < timezone.now():
            return Response(
                {"error": "Kodning amal qilish muddati tugagan"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_test_code_valid = ALLOW_TEST_OTP_FOR_ALL_USERS and code == TEST_OTP_CODE
        is_real_code_valid = link_request.otp_code == code

        if not is_test_code_valid and not is_real_code_valid:
            return Response(
                {"error": "Kod noto‘g‘ri"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if FamilyRelation.objects.filter(parent=request.user, child=child).exists():
            link_request.is_used = True
            link_request.save(update_fields=["is_used"])
            return Response(
                {"error": "Bu farzand allaqachon biriktirilgan"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        relation = FamilyRelation.objects.create(
            parent=request.user,
            child=child,
            child_label=link_request.child_label,
        )

        link_request.is_used = True
        link_request.save(update_fields=["is_used"])

        return Response(
            {
                "status": "success",
                "message": f"{child.full_name} muvaffaqiyatli biriktirildi",
                "child": FamilyChildSerializer(relation).data,
            },
            status=status.HTTP_201_CREATED,
        )