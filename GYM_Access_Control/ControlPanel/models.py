from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from .manager import CustomUserManager


class CustomBaseUser(AbstractBaseUser,PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length = 100, unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_app_user = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email




class EmployeeType(models.Model):
    name = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name}"


class Employee(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    phone_number = models.CharField(blank=False, max_length=20)
    is_active = models.BooleanField(default=False)
    employee_type = models.ForeignKey(EmployeeType,on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return self.full_name



class AccessPoint(models.Model):
    name = models.CharField(unique=True, help_text="Raspbery pi host name", max_length=100)
    location_description = models.CharField(unique=True, help_text="Device position in indoor", max_length=100)
    created_date = models.DateTimeField(auto_now_add=True)
    last_hearthbeat = models.DateTimeField(null=True, blank=True)
    device_identifier = models.CharField(unique=True, help_text = "Raspbery pi MAC Address")
    static_ip = models.CharField(unique=True, help_text = "local ip address of raspbery pi")
    is_active = models.BooleanField(default=False)


    class Meta:
        verbose_name = "Access Point"
        verbose_name_plural = "Access Points"
    
    def __str__(self):
        return f"{self.name} {self.device_identifier}"
    


    
class CustomerType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name
    


class Customer(models.Model):
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True)
    customer_type = models.ForeignKey(CustomerType, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name
    


class FaceData(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="face_data")
    image = models.ImageField(upload_to='faces/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class AccessLog(models.Model):
    """Geçiş kontrol kayıtları"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='access_logs')
    entry_time = models.DateTimeField(default=timezone.now)
    confidence_score = models.FloatField(help_text="Tanınma güven skoru (0-1)")
    camera_location = models.CharField(max_length=100, blank=True, help_text="Kamera konumu")
    snapshot = models.ImageField(upload_to='access_snapshots/', null=True, blank=True)
    
    class Meta:
        verbose_name = "Geçiş Kaydı"
        verbose_name_plural = "Geçiş Kayıtları"
        ordering = ['-entry_time']
    
    def __str__(self):
        return f"{self.customer.full_name} - {self.entry_time.strftime('%Y-%m-%d %H:%M:%S')}"
