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
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# --- RO'YXATDAN O'TISH ---
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny] # Ochiq qolishi shart

    def perform_create(self, serializer):
        otp_code = str(random.randint(100000, 999999))
        user = serializer.save(otp_code=otp_code)
        # O'zbekiston vaqti bilan terminalga chiqarish
        print(f"\n[{timezone.now()}] >>>> SMS YUBORILDI {user.phone}: {otp_code} <<<<\n")

# --- KODNI TASDIQLASH (VERIFY) ---
class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny] # Ochiq qolishi shart

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
    permission_classes = [permissions.AllowAny] # Ochiq qolishi shart

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
class LocationAPIView(generics.ListCreateAPIView):
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated] # FAQAT LOGIN QILGANLARGA

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('phone', openapi.IN_QUERY, description="Telefon raqam", type=openapi.TYPE_STRING),
            openapi.Parameter('period', openapi.IN_QUERY, description="Kunlar (1, 7, 30)", type=openapi.TYPE_INTEGER),
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
            # O'zbekiston vaqt zonasini hisobga oladi
            start_date = timezone.now() - timedelta(days=int(period))
            queryset = queryset.filter(created_at__gte=start_date)
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        # Login qilgan userning o'ziga bog'laymiz
        serializer.save(user=self.request.user)

# --- APP USAGE (ILOVA NAZORATI) ---
class AppUsageAPIView(generics.ListCreateAPIView):
    serializer_class = AppUsageSerializer
    permission_classes = [permissions.IsAuthenticated] # FAQAT LOGIN QILGANLARGA

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('phone', openapi.IN_QUERY, description="Telefon raqam", type=openapi.TYPE_STRING),
            openapi.Parameter('period', openapi.IN_QUERY, description="Kunlar (1, 7, 30)", type=openapi.TYPE_INTEGER),
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

    def perform_create(self, serializer):
        # Login qilgan userning o'ziga bog'laymiz
        serializer.save(user=self.request.user)