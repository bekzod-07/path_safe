import random
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import authenticate

from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token

from .models import User, UserLocation, AppUsage, FamilyRelation
from .serializers import (
    RegisterSerializer, 
    UserSerializer, 
    LoginSerializer, 
    VerifyOTPSerializer, 
    LocationSerializer,
    AppUsageSerializer
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# --- RO'YXATDAN O'TISH ---
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        otp_code = str(random.randint(100000, 999999))
        user = serializer.save(otp_code=otp_code)
        print(f"\n[{timezone.now()}] >>>> SMS YUBORILDI {user.phone}: {otp_code} <<<<\n")

# --- KODNI TASDIQLASH (VERIFY) ---
class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            code = serializer.validated_data['code']
            
            user = User.objects.filter(phone=phone, otp_code=code).first()
            if user:
                user.is_verified = True
                user.save()
                return Response({"message": "Muvaffaqiyatli tasdiqlandi!"}, status=status.HTTP_200_OK)
            return Response({"error": "Kod noto'g'ri!"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- KIRISH (LOGIN) ---
class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data.get('phone')
            password = serializer.validated_data.get('password')
            
            user = authenticate(phone=phone, password=password)
            if user:
                token, _ = Token.objects.get_or_create(user=user)
                return Response({
                    "token": token.key,
                    "full_name": user.full_name,
                    "role": user.role
                }, status=status.HTTP_200_OK)
            return Response({"error": "Telefon yoki parol xato!"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- FARZANDNI BIRIKTIRISH (OTA-ONA UCHUN) ---
class AddChildView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['child_phone'],
            properties={'child_phone': openapi.Schema(type=openapi.TYPE_STRING, description="Farzand telefon raqami")}
        )
    )
    def post(self, request):
        if request.user.role != 'parent':
            return Response({"error": "Faqat ota-onalar farzand qo'sha oladi"}, status=status.HTTP_403_FORBIDDEN)
        
        child_phone = request.data.get('child_phone')
        child = User.objects.filter(phone=child_phone, role='child').first()
        
        if not child:
            return Response({"error": "Bunday raqamli farzand topilmadi yoki u 'Farzand' rolida emas"}, status=status.HTTP_404_NOT_FOUND)
        
        relation, created = FamilyRelation.objects.get_or_create(parent=request.user, child=child)
        if not created:
            return Response({"message": "Bu farzand allaqachon biriktirilgan"}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({"message": f"{child.full_name} muvaffaqiyatli biriktirildi"}, status=status.HTTP_201_CREATED)

# --- GEOLOKATSIYA (LOCATION) ---
class LocationAPIView(generics.ListCreateAPIView):
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('phone', openapi.IN_QUERY, description="Telefon raqam", type=openapi.TYPE_STRING),
            openapi.Parameter('period', openapi.IN_QUERY, description="Kunlar (1, 7, 30)", type=openapi.TYPE_INTEGER),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        phone = self.request.query_params.get('phone')
        period = self.request.query_params.get('period')
        
        if user.role == 'parent':
            queryset = UserLocation.objects.filter(user__parent_relation__parent=user)
        else:
            queryset = UserLocation.objects.filter(user=user)

        if phone:
            queryset = queryset.filter(user__phone=phone)
        if period:
            start_date = timezone.now() - timedelta(days=int(period))
            queryset = queryset.filter(created_at__gte=start_date)
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# --- APP USAGE (ILOVA NAZORATI) ---
class AppUsageAPIView(generics.ListCreateAPIView):
    serializer_class = AppUsageSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('phone', openapi.IN_QUERY, description="Telefon raqam", type=openapi.TYPE_STRING),
            openapi.Parameter('period', openapi.IN_QUERY, description="Kunlar (1, 7, 30)", type=openapi.TYPE_INTEGER),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        phone = self.request.query_params.get('phone')
        period = self.request.query_params.get('period')
        
        if user.role == 'parent':
            queryset = AppUsage.objects.filter(user__parent_relation__parent=user)
        else:
            queryset = AppUsage.objects.filter(user=user)

        if phone:
            queryset = queryset.filter(user__phone=phone)
        if period:
            start_date = timezone.now() - timedelta(days=int(period))
            queryset = queryset.filter(created_at__gte=start_date)
            
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)