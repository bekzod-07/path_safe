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
    AppUsageSerializer,
    ChildSerializer
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

from rest_framework.generics import ListAPIView
from rest_framework.views import APIView

# --- FARZANDLARNI BOSHQARISH (GET, POST, DELETE) ---
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import User, FamilyRelation
from .serializers import ChildSerializer

class FamilyManagementView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    # 1. FARZANDLAR RO'YXATI (GET)
    @swagger_auto_schema(
        tags=['family'],
        operation_summary="Ota-onaga biriktirilgan farzandlar ro'yxati",
        manual_parameters=[
            openapi.Parameter('child_phone', openapi.IN_QUERY, type=openapi.TYPE_STRING, description="Muayyan farzandni raqami orqali qidirish (ixtiyoriy)")
        ]
    )
    
    def get(self, request):
            # Agar parent_phone query-da kelsa, o'sha ota-onaning farzandlarini olamiz
            p_phone = request.query_params.get('parent_phone')
            child_phone = request.query_params.get('child_phone')

            if p_phone:
                # Telefon raqami orqali ota-onani topamiz
                queryset = User.objects.filter(parent_relation__parent__phone=p_phone)
            else:
                # Agar telefon berilmasa, login qilgan foydalanuvchinikini olamiz
                queryset = User.objects.filter(parent_relation__parent=request.user)
            
            if child_phone:
                queryset = queryset.filter(phone=child_phone)
                
            serializer = ChildSerializer(queryset, many=True, context={'request': request})
            return Response(serializer.data)

    # 2. BIRIKTIRISH (POST)
    @swagger_auto_schema(
        tags=['family'],
        operation_summary="Ota-onaga farzandni telefon raqamlar orqali biriktirish",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['parent_phone', 'child_phone', 'child_label'],
            properties={
                'parent_phone': openapi.Schema(type=openapi.TYPE_STRING, example="+998901112233"),
                'child_phone': openapi.Schema(type=openapi.TYPE_STRING, example="+998995577784"),
                'child_label': openapi.Schema(type=openapi.TYPE_STRING, example="O'g'lim Bekzod")
            }
        )
    )
    def post(self, request):
        p_phone = request.data.get('parent_phone')
        c_phone = request.data.get('child_phone')
        label = request.data.get('child_label')

        if not all([p_phone, c_phone, label]):
            return Response({"error": "Barcha maydonlarni to'ldiring!"}, status=status.HTTP_400_BAD_REQUEST)

        parent = User.objects.filter(phone=p_phone, role='parent').first()
        child = User.objects.filter(phone=c_phone, role='child').first()

        if not parent:
            return Response({"error": "Ota-ona topilmadi!"}, status=status.HTTP_404_NOT_FOUND)
        if not child:
            return Response({"error": "Bunday raqamli farzand topilmadi!"}, status=status.HTTP_404_NOT_FOUND)

        relation, created = FamilyRelation.objects.update_or_create(
            parent=parent,
            child=child,
            defaults={'child_label': label}
        )

        msg = "biriktirildi" if created else "ma'lumotlari yangilandi"
        return Response({
            "status": "success",
            "message": f"{parent.full_name}ga {child.full_name} ({label}) {msg}!"
        }, status=status.HTTP_201_CREATED)

    # 3. O'CHIRISH (DELETE)
    @swagger_auto_schema(
        tags=['family'],
        operation_summary="Farzandni ota-onadan raqamlar orqali uzish",
        manual_parameters=[
            openapi.Parameter('parent_phone', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True, description="Ota-ona telefon raqami"),
            openapi.Parameter('child_phone', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=True, description="Farzand telefon raqami")
        ]
    )
    def delete(self, request):
        p_phone = request.query_params.get('parent_phone')
        c_phone = request.query_params.get('child_phone')

        if not p_phone or not c_phone:
            return Response({"error": "Ota-ona va farzand raqami yuborilishi shart!"}, status=status.HTTP_400_BAD_REQUEST)

        relation = FamilyRelation.objects.filter(
            parent__phone=p_phone, 
            child__phone=c_phone
        ).first()
        
        if relation:
            relation.delete()
            return Response({"message": "Farzand muvaffaqiyatli olib tashlandi"}, status=status.HTTP_200_OK)
        
        return Response({"error": "Bunday birikma topilmadi"}, status=status.HTTP_404_NOT_FOUND)