from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('Telefon raqam bo\'lishi shart')
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone, password, **extra_fields)

class User(AbstractUser):
    # Rol variantlari
    ROLE_CHOICES = (
        ('parent', 'Ota-ona'),
        ('child', 'Farzand'),
    )

    username = None
    phone = models.CharField(max_length=15, unique=True, verbose_name="Telefon raqam")
    full_name = models.CharField(max_length=100, verbose_name="F.I.SH")
    
    # Yangi qo'shilgan rol maydoni
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES, 
        default='parent', 
        verbose_name="Rol"
    )
    
    is_verified = models.BooleanField(default=False, verbose_name="Tasdiqlangan")
    otp_code = models.CharField(max_length=6, blank=True, null=True, verbose_name="OTP kod")

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    # REQUIRED_FIELDS ga role qo'shildi (createsuperuser uchun ham kerak bo'ladi)
    REQUIRED_FIELDS = ['full_name', 'role']

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"
    
class FamilyRelation(models.Model):
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='children_relations')
    child = models.ForeignKey(User, on_delete=models.CASCADE, related_name='parent_relation')
    child_label = models.CharField(max_length=100, help_text="Masalan: O'g'lim Ali") # Ism qo'shish uchun
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('parent', 'child')

    def __str__(self):
        return f"{self.parent.full_name} -> {self.child.full_name}"

class UserLocation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='locations', verbose_name="Foydalanuvchi")
    lat = models.FloatField(verbose_name="Kenglik (lat)")
    lng = models.FloatField(verbose_name="Uzunlik (lng)")
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Manzil")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")

    class Meta:
        verbose_name = "Geolokatsiya"
        verbose_name_plural = "Geolokatsiyalar"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.full_name} | {self.lat}, {self.lng}"
    
class AppUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='app_usages', verbose_name="Foydalanuvchi")
    app_name = models.CharField(max_length=255, verbose_name="Ilova nomi")
    usage_time = models.IntegerField(verbose_name="Foydalanish vaqti (daqiqa)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan vaqt")

    class Meta:
        verbose_name = "Ilova nazorati"
        verbose_name_plural = "Ilova nazoratlari"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.app_name} - {self.usage_time} min ({self.user.phone})"