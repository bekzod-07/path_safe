from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

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
        return self.create_user(phone, password, **extra_fields)

class User(AbstractUser):
    username = None
    phone = models.CharField(max_length=15, unique=True)
    full_name = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    otp_code = models.CharField(max_length=6, blank=True, null=True)

    objects = UserManager() # Yangi managerni ulaymiz

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return self.phone
    
class UserLocation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='locations')
    lat = models.FloatField() # Kenglik
    lng = models.FloatField() # Uzunlik
    address = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.phone} - {self.lat}, {self.lng}"
    
class AppUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='app_usages')
    app_name = models.CharField(max_length=255) # Ilova nomi (masalan: Instagram)
    usage_time = models.IntegerField() # Sekundlarda yoki minutlarda
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.app_name} - {self.usage_time} min"