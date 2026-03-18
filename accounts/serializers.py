from rest_framework import serializers
from .models import User, UserLocation, AppUsage, FamilyRelation, FamilyLinkRequest


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "full_name", "phone", "role", "is_verified"]


class UserProfileSerializer(serializers.ModelSerializer):
    date_joined = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = User
        fields = ["id", "full_name", "phone", "role", "is_verified", "date_joined"]
        read_only_fields = ["id", "is_verified", "date_joined"]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["full_name", "phone", "role"]

    def validate_full_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Ism bo‘sh bo‘lmasligi kerak")
        return value

    def validate_phone(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Telefon raqam bo‘sh bo‘lmasligi kerak")

        qs = User.objects.filter(phone=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError("Bu telefon raqam allaqachon mavjud")
        return value

    def validate_role(self, value):
        user = self.instance
        if user and value != user.role:
            has_family_links = (
                FamilyRelation.objects.filter(parent=user).exists()
                or FamilyRelation.objects.filter(child=user).exists()
            )
            if has_family_links:
                raise serializers.ValidationError(
                    "Rolni o‘zgartirishdan oldin family bog‘lanishlarini olib tashlang"
                )
        return value


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=4)

    class Meta:
        model = User
        fields = ["full_name", "phone", "password", "role"]

    def validate_full_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Ism bo‘sh bo‘lmasligi kerak")
        return value

    def validate_phone(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Telefon raqam bo‘sh bo‘lmasligi kerak")

        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("Bu telefon raqam allaqachon ro‘yxatdan o‘tgan")
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

    def validate_phone(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Telefon raqam bo‘sh bo‘lmasligi kerak")
        return value

    def validate_code(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Kod bo‘sh bo‘lmasligi kerak")
        return value


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField()

    def validate_phone(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Telefon raqam bo‘sh bo‘lmasligi kerak")
        return value

    def validate_password(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Parol bo‘sh bo‘lmasligi kerak")
        return value


class LocationSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(write_only=True, required=True)
    user_phone = serializers.CharField(source="user.phone", read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    user_role = serializers.CharField(source="user.role", read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = UserLocation
        fields = [
            "id",
            "phone",
            "user_phone",
            "full_name",
            "user_role",
            "lat",
            "lng",
            "address",
            "created_at",
        ]

    def validate_phone(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Telefon raqam bo‘sh bo‘lmasligi kerak")
        return value


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

    def validate_phone(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Telefon raqam bo‘sh bo‘lmasligi kerak")
        return value

    def validate_app_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Ilova nomi bo‘sh bo‘lmasligi kerak")
        return value

    def validate_usage_time(self, value):
        if value < 0:
            raise serializers.ValidationError("Usage time manfiy bo‘lishi mumkin emas")
        return value


class FamilyChildSerializer(serializers.ModelSerializer):
    child_id = serializers.IntegerField(source="child.id", read_only=True)
    full_name = serializers.CharField(source="child.full_name", read_only=True)
    phone = serializers.CharField(source="child.phone", read_only=True)
    is_verified = serializers.BooleanField(source="child.is_verified", read_only=True)
    label = serializers.CharField(source="child_label", read_only=True)
    status = serializers.SerializerMethodField()
    linked_at = serializers.DateTimeField(
        source="created_at",
        format="%Y-%m-%d %H:%M:%S",
        read_only=True,
    )
    request_expires_at = serializers.SerializerMethodField()

    class Meta:
        model = FamilyRelation
        fields = [
            "child_id",
            "full_name",
            "phone",
            "is_verified",
            "label",
            "status",
            "linked_at",
            "request_expires_at",
        ]

    def get_status(self, obj):
        return "tasdiqlangan"

    def get_request_expires_at(self, obj):
        return None


class FamilyPendingSerializer(serializers.ModelSerializer):
    child_id = serializers.IntegerField(source="child.id", read_only=True)
    full_name = serializers.CharField(source="child.full_name", read_only=True)
    phone = serializers.CharField(source="child.phone", read_only=True)
    is_verified = serializers.BooleanField(source="child.is_verified", read_only=True)
    label = serializers.CharField(source="child_label", read_only=True)
    status = serializers.SerializerMethodField()
    linked_at = serializers.SerializerMethodField()
    request_expires_at = serializers.DateTimeField(
        source="expires_at",
        format="%Y-%m-%d %H:%M:%S",
        read_only=True,
    )

    class Meta:
        model = FamilyLinkRequest
        fields = [
            "child_id",
            "full_name",
            "phone",
            "is_verified",
            "label",
            "status",
            "linked_at",
            "request_expires_at",
        ]

    def get_status(self, obj):
        return "tasdiqlanmagan"

    def get_linked_at(self, obj):
        return None


class FamilyRequestSerializer(serializers.Serializer):
    child_phone = serializers.CharField()
    child_name = serializers.CharField()
    child_label = serializers.CharField(max_length=100)

    def validate_child_phone(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Farzand telefon raqami bo‘sh bo‘lmasligi kerak")
        return value

    def validate_child_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Farzand ismi bo‘sh bo‘lmasligi kerak")
        return value

    def validate_child_label(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Farzand label bo‘sh bo‘lmasligi kerak")
        return value


class FamilyVerifySerializer(serializers.Serializer):
    child_phone = serializers.CharField()
    code = serializers.CharField()

    def validate_child_phone(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Farzand telefon raqami bo‘sh bo‘lmasligi kerak")
        return value

    def validate_code(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Kod bo‘sh bo‘lmasligi kerak")
        return value


class FamilyUpdateSerializer(serializers.Serializer):
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
            raise serializers.ValidationError("Yangi label bo‘sh bo‘lmasligi kerak")
        return value


class FamilyDeleteSerializer(serializers.Serializer):
    child_phone = serializers.CharField()

    def validate_child_phone(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Farzand telefon raqami bo‘sh bo‘lmasligi kerak")
        return value


class FamilyLinkRequestSerializer(serializers.ModelSerializer):
    parent_full_name = serializers.CharField(source="parent.full_name", read_only=True)
    parent_phone = serializers.CharField(source="parent.phone", read_only=True)
    child_full_name = serializers.CharField(source="child.full_name", read_only=True)
    child_phone = serializers.CharField(source="child.phone", read_only=True)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    expires_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = FamilyLinkRequest
        fields = [
            "id",
            "parent_full_name",
            "parent_phone",
            "child_full_name",
            "child_phone",
            "child_label",
            "is_used",
            "created_at",
            "updated_at",
            "expires_at",
        ]