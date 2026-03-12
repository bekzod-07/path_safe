from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import User, UserLocation, AppUsage, FamilyRelation


# =========================
# INLINE'lar
# =========================

class FamilyRelationInline(admin.TabularInline):
    model = FamilyRelation
    fk_name = "parent"
    extra = 0
    autocomplete_fields = ("child",)
    fields = ("child", "child_label", "created_at")
    readonly_fields = ("created_at",)
    verbose_name = "Biriktirilgan farzand"
    verbose_name_plural = "Biriktirilgan farzandlar"


class ChildRelationInline(admin.TabularInline):
    model = FamilyRelation
    fk_name = "child"
    extra = 0
    autocomplete_fields = ("parent",)
    fields = ("parent", "child_label", "created_at")
    readonly_fields = ("created_at",)
    verbose_name = "Biriktirilgan ota-ona"
    verbose_name_plural = "Biriktirilgan ota-onalar"


class UserLocationInline(admin.TabularInline):
    model = UserLocation
    extra = 0
    fields = ("lat", "lng", "address", "created_at")
    readonly_fields = ("lat", "lng", "address", "created_at")
    can_delete = False
    verbose_name = "Lokatsiya"
    verbose_name_plural = "So‘nggi lokatsiyalar"
    ordering = ("-created_at",)


class AppUsageInline(admin.TabularInline):
    model = AppUsage
    extra = 0
    fields = ("app_name", "usage_time", "created_at")
    readonly_fields = ("app_name", "usage_time", "created_at")
    can_delete = False
    verbose_name = "App usage"
    verbose_name_plural = "Ilova ishlatilishlari"
    ordering = ("-created_at",)


# =========================
# USER ADMIN
# =========================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    list_display = (
        "id",
        "full_name",
        "phone",
        "role",
        "verified_badge",
        "parent_count",
        "child_count",
        "is_staff",
        "is_active",
        "date_joined",
    )
    list_filter = (
        "role",
        "is_verified",
        "is_staff",
        "is_superuser",
        "is_active",
        "date_joined",
    )
    search_fields = ("full_name", "phone")
    ordering = ("-date_joined",)
    list_per_page = 25
    autocomplete_fields = ()
    readonly_fields = (
        "date_joined",
        "last_login",
        "verification_status_text",
        "parent_count",
        "child_count",
    )

    fieldsets = (
        ("Asosiy ma'lumotlar", {
            "fields": (
                "phone",
                "password",
                "full_name",
                "role",
            )
        }),
        ("Tasdiqlash holati", {
            "fields": (
                "is_verified",
                "otp_code",
                "verification_status_text",
            )
        }),
        ("Bog‘lanishlar statistikasi", {
            "fields": (
                "parent_count",
                "child_count",
            )
        }),
        ("Ruxsatlar", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Muhim sanalar", {
            "fields": (
                "last_login",
                "date_joined",
            )
        }),
    )

    add_fieldsets = (
        ("Yangi foydalanuvchi qo‘shish", {
            "classes": ("wide",),
            "fields": (
                "full_name",
                "phone",
                "role",
                "password1",
                "password2",
                "is_verified",
                "is_active",
                "is_staff",
            ),
        }),
    )

    inlines = [FamilyRelationInline, ChildRelationInline, UserLocationInline, AppUsageInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related(
            "parent_links__child",
            "child_links__parent",
        )

    @admin.display(description="Tasdiq")
    def verified_badge(self, obj):
        if obj.is_verified:
            return format_html(
                '<span style="color: white; background: #16a34a; padding: 3px 8px; border-radius: 10px;">Tasdiqlangan</span>'
            )
        return format_html(
            '<span style="color: white; background: #dc2626; padding: 3px 8px; border-radius: 10px;">Tasdiqlanmagan</span>'
        )

    @admin.display(description="Ota-onalar soni")
    def parent_count(self, obj):
        try:
            return obj.child_links.count()
        except Exception:
            return 0

    @admin.display(description="Farzandlar soni")
    def child_count(self, obj):
        try:
            return obj.parent_links.count()
        except Exception:
            return 0

    @admin.display(description="Holat")
    def verification_status_text(self, obj):
        if obj.is_verified:
            return "Foydalanuvchi tasdiqlangan"
        if obj.otp_code:
            return f"OTP kutilmoqda: {obj.otp_code}"
        return "Tasdiqlanmagan"


# =========================
# FAMILY RELATION ADMIN
# =========================

@admin.register(FamilyRelation)
class FamilyRelationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "parent",
        "parent_phone",
        "child",
        "child_phone",
        "child_label",
        "child_verified",
        "created_at",
    )
    list_filter = (
        "created_at",
        "parent__is_verified",
        "child__is_verified",
        "parent__role",
        "child__role",
    )
    search_fields = (
        "parent__full_name",
        "parent__phone",
        "child__full_name",
        "child__phone",
        "child_label",
    )
    autocomplete_fields = ("parent", "child")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
    list_select_related = ("parent", "child")
    list_per_page = 25

    fieldsets = (
        ("Biriktirish ma'lumotlari", {
            "fields": (
                "parent",
                "child",
                "child_label",
                "created_at",
            )
        }),
    )

    @admin.display(description="Ota-ona raqami")
    def parent_phone(self, obj):
        return obj.parent.phone

    @admin.display(description="Farzand raqami")
    def child_phone(self, obj):
        return obj.child.phone

    @admin.display(description="Farzand holati")
    def child_verified(self, obj):
        if obj.child.is_verified:
            return "Tasdiqlangan"
        return "Tasdiqlanmagan"


# =========================
# USER LOCATION ADMIN
# =========================

@admin.register(UserLocation)
class UserLocationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "user_phone",
        "user_role",
        "lat",
        "lng",
        "address_short",
        "created_at",
    )
    list_filter = (
        "created_at",
        "user__role",
        "user__is_verified",
    )
    search_fields = (
        "user__full_name",
        "user__phone",
        "address",
    )
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
    list_select_related = ("user",)
    list_per_page = 30

    @admin.display(description="Telefon")
    def user_phone(self, obj):
        return obj.user.phone

    @admin.display(description="Rol")
    def user_role(self, obj):
        return obj.user.role

    @admin.display(description="Manzil")
    def address_short(self, obj):
        if not obj.address:
            return "-"
        return obj.address[:50] + ("..." if len(obj.address) > 50 else "")


# =========================
# APP USAGE ADMIN
# =========================

@admin.register(AppUsage)
class AppUsageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "user_phone",
        "user_role",
        "app_name",
        "usage_time",
        "created_at",
    )
    list_filter = (
        "created_at",
        "user__role",
        "user__is_verified",
        "app_name",
    )
    search_fields = (
        "user__full_name",
        "user__phone",
        "app_name",
    )
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
    list_select_related = ("user",)
    list_per_page = 30

    @admin.display(description="Telefon")
    def user_phone(self, obj):
        return obj.user.phone

    @admin.display(description="Rol")
    def user_role(self, obj):
        return obj.user.role