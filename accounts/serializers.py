from rest_framework import serializers
from .models import User

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
            is_active=True # SMS tasdiqlanguncha login qila olmasligi uchun False qilsa ham bo'ladi
        )
        # Bu yerda SMS yuborish funksiyasini chaqirasiz (masalan, Eskiz API)
        # user.otp_code = "123456" 
        # user.save()
        return user

class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.CharField()

class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField()

from .models import User, UserLocation, AppUsage

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'phone', 'is_verified']

class LocationSerializer(serializers.ModelSerializer):
    # phone endi faqat o'qish uchun emas, yuborish uchun ham ishlaydi
    phone = serializers.CharField(source='user.phone', required=False)

    class Meta:
        model = UserLocation
        fields = ['id', 'phone', 'lat', 'lng', 'address', 'created_at']

class AppUsageSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(write_only=True) # POST uchun kerak

    class Meta:
        model = AppUsage
        fields = ['id', 'phone', 'app_name', 'usage_time', 'created_at']

    def create(self, validated_data):
        phone = validated_data.pop('phone')
        from .models import User
        user = User.objects.filter(phone=phone).first()
        if not user:
            raise serializers.ValidationError({"phone": "Foydalanuvchi topilmadi"})
        
        usage = AppUsage.objects.create(user=user, **validated_data)
        return usage