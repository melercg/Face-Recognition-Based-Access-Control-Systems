from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomBaseUser
from .models import AccessPoint
from .models import Customer
from .models import CustomerType
from .models import FaceData
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

class CustomUserAdmin(UserAdmin):
    model = CustomBaseUser
    list_display = ('email', 'username', 'is_staff', 'is_app_user')
    list_filter = ('is_staff', 'is_app_user', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Kişisel Bilgiler', {'fields': ('username',)}),
        ('Yetkiler', {'fields': ('is_staff', 'is_app_user', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_staff', 'is_app_user', 'is_active')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email','last_login')



class CustomerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'customer_type',)
    list_filter = ('is_active', 'full_name',)
    ordering = ('created_at',)
    search_fields = ('phone_number',)



class CustomerTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


class AccessPointsAdmin(admin.ModelAdmin):
    list_display = ('name', 'location_description', 'created_date', 'device_identifier')
    list_filter = ('is_active',)
    readonly_fields = ('created_date', 'last_hearthbeat')
    ordering = ('last_hearthbeat',)
    search_fields = ('name',)


class FaceDataAdmin(admin.ModelAdmin):
    list_display = ('customer',)
    search_fields = ('customer',)
    ordering = ('customer',)


admin.site.register(CustomBaseUser, CustomUserAdmin)
admin.site.register(AccessPoint,AccessPointsAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(CustomerType, CustomerTypeAdmin)
admin.site.register(FaceData, FaceDataAdmin)
