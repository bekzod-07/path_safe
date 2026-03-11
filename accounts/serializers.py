from rest_framework import serializers
from django.utils import timezone
from .models import User, UserLocation, AppUsage

# --- FOYDALANUVCHI SERIALIZER ---
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'phone', 'is_verified']

# --- RO'YXATDAN O'TISH ---
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['full_name', 'phone', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            phone=validated_data['phone'],
            full_name=validated_data['full_name'],
            password=validated_data['password'],
            is_active=True # Hozircha True, xohlasangiz False qilib OTPdan keyin yoqasiz
        )
        return user

# --- OTP VA LOGIN ---
class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.CharField()

class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField()

# --- GEOLOKATSIYA (LOCATION) ---
class LocationSerializer(serializers.ModelSerializer):
    # GET so'rovda telefon raqamni ko'rish uchun
    phone = serializers.CharField(source='user.phone', read_only=True)
    # Ma'lumot qachon kelganini chiroyli formatda ko'rish uchun
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = UserLocation
        fields = ['id', 'phone', 'lat', 'lng', 'address', 'created_at']

# --- ILOVA NAZORATI (APP USAGE) ---
class AppUsageSerializer(serializers.ModelSerializer):
    # Ma'lumot yuborilayotganda telefon raqam orqali userni topish uchun
    phone = serializers.CharField(write_only=True, required=False)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = AppUsage
        fields = ['id', 'phone', 'user_phone', 'app_name', 'usage_time', 'created_at']

    def create(self, validated_data):
        # Agar viewdan user kelmasa, yuborilgan phone orqali topamiz
        phone = validated_data.pop('phone', None)
        request = self.context.get('request')

        if request and request.user.is_authenticated:
            user = request.user
        elif phone:
            user = User.objects.filter(phone=phone).first()
        else:
            raise serializers.ValidationError({"error": "Foydalanuvchi aniqlanmadi"})

        if not user:
            raise serializers.ValidationError({"phone": "Bunday foydalanuvchi mavjud emas"})

        return AppUsage.objects.create(user=user, **validated_data)