import random
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import authenticate

from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token

from .models import User, UserLocation, AppUsage
from .serializers import (
    RegisterSerializer, 
    UserSerializer, 
    LoginSerializer, 
    VerifyOTPSerializer, 
    LocationSerializer,
    AppUsageSerializer
)

# --- RO'YXATDAN O'TISH ---
class RegisterView(generics.CreateAPIView):
    """
    Ism, telefon va parol orqali ro'yxatdan o'tish.
    Ro'yxatdan o'tganda terminalda OTP kod ko'rinadi.
    """
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        # 6 xonali tasodifiy kod yaratish
        otp_code = str(random.randint(100000, 999999))
        user = serializer.save(otp_code=otp_code)
        # Hozircha terminalga chiqaramiz (Eskiz ulanmagan bo'lsa)
        print(f"\n>>>> SMS YUBORILDI {user.phone} RAQAMIGA: {otp_code} <<<<\n")

# --- KODNI TASDIQLASH (VERIFY) ---
class VerifyOTPView(APIView):
    """
    Telefon va yuborilgan kodni tekshirish.
    """
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
    """
    Telefon va parol orqali kirish.
    Muvaffaqiyatli kirilsa Token va ism qaytadi.
    """
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
                    "full_name": user.full_name
                }, status=status.HTTP_200_OK)
            
            return Response({"error": "Telefon yoki parol xato!"}, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- GEOLOKATSIYA (LOCATION) ---
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class LocationAPIView(generics.ListCreateAPIView):
    serializer_class = LocationSerializer
    # Test jarayonida xatolik bermasligi uchun ruxsatni ochiq qilamiz
    permission_classes = [permissions.AllowAny] 

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('phone', openapi.IN_QUERY, description="Telefon raqam (+998953281507)", type=openapi.TYPE_STRING),
            openapi.Parameter('period', openapi.IN_QUERY, description="Kunlar (1, 7, 30, 365)", type=openapi.TYPE_INTEGER),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        phone = self.request.query_params.get('phone')
        period = self.request.query_params.get('period')
        
        queryset = UserLocation.objects.all()
        if phone:
            queryset = queryset.filter(user__phone=phone)
        if period:
            start_date = timezone.now() - timedelta(days=int(period))
            queryset = queryset.filter(created_at__gte=start_date)
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        # Agar login qilmagan bo'lsa, POST so'rovda yuborilgan phone orqali userni topamiz
        phone = self.request.data.get('phone')
        if phone:
            user = User.objects.filter(phone=phone).first()
            if user:
                serializer.save(user=user)
                return
        # Aks holda hozirgi userga
        serializer.save(user=self.request.user if self.request.user.is_authenticated else None)

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class AppUsageAPIView(generics.ListCreateAPIView):
    serializer_class = AppUsageSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('phone', openapi.IN_QUERY, description="Telefon (+998953281507)", type=openapi.TYPE_STRING),
            openapi.Parameter('period', openapi.IN_QUERY, description="Kunlar (1, 7, 30, 365)", type=openapi.TYPE_INTEGER),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        phone = self.request.query_params.get('phone')
        period = self.request.query_params.get('period')
        
        queryset = AppUsage.objects.all()
        if phone:
            queryset = queryset.filter(user__phone=phone)
        if period:
            start_date = timezone.now() - timedelta(days=int(period))
            queryset = queryset.filter(created_at__gte=start_date)
            
        return queryset.order_by('-created_at')