from rest_framework import serializers
from .models import User, UserLocation, AppUsage, FamilyRelation

# --- FOYDALANUVCHI SERIALIZER ---
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'phone', 'role', 'is_verified']

# --- RO'YXATDAN O'TISH ---
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['full_name', 'phone', 'password', 'role'] # 'role' qo'shildi

    def create(self, validated_data):
        # validated_data ichida 'role' ham keladi
        user = User.objects.create_user(
            phone=validated_data['phone'],
            full_name=validated_data['full_name'],
            password=validated_data['password'],
            role=validated_data.get('role', 'parent'), # Rolni saqlash
            is_active=True 
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
    phone = serializers.CharField(source='user.phone', read_only=True)
    user_role = serializers.CharField(source='user.role', read_only=True) # Rolni ko'rish foydali
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = UserLocation
        fields = ['id', 'phone', 'user_role', 'lat', 'lng', 'address', 'created_at']

# --- ILOVA NAZORATI (APP USAGE) ---
class AppUsageSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(write_only=True, required=False)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = AppUsage
        fields = ['id', 'phone', 'user_phone', 'app_name', 'usage_time', 'created_at']

    def create(self, validated_data):
        phone = validated_data.pop('phone', None)
        request = self.context.get('request')

        # Avval requestdagi foydalanuvchini tekshiramiz
        if request and request.user.is_authenticated:
            user = request.user
        elif phone:
            user = User.objects.filter(phone=phone).first()
        else:
            raise serializers.ValidationError({"error": "Foydalanuvchi aniqlanmadi"})

        if not user:
            raise serializers.ValidationError({"phone": "Bunday foydalanuvchi mavjud emas"})

        return AppUsage.objects.create(user=user, **validated_data)
    
class ChildSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'full_name', 'phone', 'is_verified', 'label']

    def get_label(self, obj):
        # Hozirgi login qilgan ota-ona bergan nomni olamiz
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            relation = FamilyRelation.objects.filter(parent=request.user, child=obj).first()
            return relation.child_label if relation else ""
        return ""
    

    