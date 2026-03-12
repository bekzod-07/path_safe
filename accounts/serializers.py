from rest_framework import serializers
from .models import User, UserLocation, AppUsage, FamilyRelation


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "full_name", "phone", "role", "is_verified"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=4)

    class Meta:
        model = User
        fields = ["full_name", "phone", "password", "role"]

    def validate_phone(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Telefon raqam bo‘sh bo‘lmasligi kerak")
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            phone=validated_data["phone"],
            full_name=validated_data["full_name"],
            password=validated_data["password"],
            role=validated_data.get("role", User.ROLE_PARENT),
            is_active=True,
        )


class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField()


class LocationSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(write_only=True, required=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    user_role = serializers.CharField(source="user.role", read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = UserLocation
        fields = [
            "id",
            "phone",
            "full_name",
            "user_role",
            "lat",
            "lng",
            "address",
            "created_at",
        ]


class AppUsageSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(write_only=True, required=True)
    user_phone = serializers.CharField(source="user.phone", read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    user_role = serializers.CharField(source="user.role", read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = AppUsage
        fields = [
            "id",
            "phone",
            "user_phone",
            "full_name",
            "user_role",
            "app_name",
            "usage_time",
            "created_at",
            "updated_at",
        ]


class FamilyChildSerializer(serializers.ModelSerializer):
    child_id = serializers.IntegerField(source="child.id", read_only=True)
    full_name = serializers.CharField(source="child.full_name", read_only=True)
    phone = serializers.CharField(source="child.phone", read_only=True)
    is_verified = serializers.BooleanField(source="child.is_verified", read_only=True)
    label = serializers.CharField(source="child_label", read_only=True)
    linked_at = serializers.DateTimeField(source="created_at", format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = FamilyRelation
        fields = ["child_id", "full_name", "phone", "is_verified", "label", "linked_at"]


class FamilyUpsertSerializer(serializers.Serializer):
    child_phone = serializers.CharField()
    child_label = serializers.CharField(max_length=100)

    def validate_child_phone(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Farzand telefon raqami bo‘sh bo‘lmasligi kerak")
        return value

    def validate_child_label(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Farzand nomi/label bo‘sh bo‘lmasligi kerak")
        return value


class FamilyDeleteSerializer(serializers.Serializer):
    child_phone = serializers.CharField()

    def validate_child_phone(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Farzand telefon raqami bo‘sh bo‘lmasligi kerak")
        return value