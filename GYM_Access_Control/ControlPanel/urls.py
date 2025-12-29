from django.contrib import admin
from django.urls import path, include
from .views import AppUser_LoginView, access_log_dashboard, AccessLogViewSet, access_logs_view
from django.contrib.auth.views import LogoutView
from .views import Customers_View, delete_customer, CustomerFaceListView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'access-logs', AccessLogViewSet, basename='access-log')

urlpatterns = [
        path('login/', AppUser_LoginView, name='login'),
        path('logout/', LogoutView.as_view(), name='logout'),
        path('customers/' , Customers_View, name="Customers"),
        path('delete-customer/',delete_customer, name="delete-customer"),
        path('api/customers/faces/', CustomerFaceListView.as_view(),name="customer-faces"),
        path('api/', include(router.urls)),
        path('access-logs/', access_logs_view, name='access-logs'),
        path('', access_log_dashboard, name='access-dashboard')
]