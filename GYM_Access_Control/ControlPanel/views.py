from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import AppUser_LoginForm
from .models import Customer
from .models import CustomerType
from .models import FaceData
from .models import AccessLog
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializer import CustomerFaceSerializer, AccessLogSerializer, AccessLogCreateSerializer
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
import subprocess
import threading
import logging

logger = logging.getLogger(__name__)


def retrain_model_async():
    """Background'da modeli yeniden eğit"""
    try:
        import os
        import sys

        # Proje kök dizini
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        recognition_service_path = os.path.join(project_root, 'RecognitionService')
        train_script = os.path.join(recognition_service_path, 'train_model.py')

        # Ortak venv'in python'unu kullan
        venv_python = os.path.join(project_root, 'venv', 'bin', 'python')

        # Eğer venv yoksa sistem python'unu kullan
        if not os.path.exists(venv_python):
            venv_python = sys.executable

        logger.info(f"Model eğitimi başlatılıyor: {train_script}")

        result = subprocess.run(
            [venv_python, train_script],
            cwd=recognition_service_path,
            capture_output=True,
            text=True,
            timeout=300  # 5 dakika timeout
        )

        if result.returncode == 0:
            logger.info("Model eğitimi başarıyla tamamlandı")
        else:
            logger.error(f"Model eğitimi başarısız: {result.stderr}")

    except Exception as e:
        logger.error(f"Model eğitimi hatası: {e}")


def AppUser_LoginView(request):
    if request.method == "POST":
        form = AppUser_LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request,email=email,password=password)

            if user is not None and user.is_app_user:
                print(user)
                login(request, user)

                return redirect("/")
            
            else:
                messages.error(request,"Invalid login information, please try again")
    else:
        form = AppUser_LoginForm()

    return render(request,'ControlPanel/app_login.html',{'form':form})
@login_required(login_url='/login/')
def Customers_View(request):

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone_number = request.POST.get('phone_number')
        customer_type_id = request.POST.get('customer_type')
        images = request.FILES.getlist('images')
        if not (3 <= len(images) <= 7):
            return HttpResponse("Please upload between 3 and 7 images.")

        customer=  Customer.objects.create(
            full_name=full_name,
            phone_number=phone_number,
            customer_type_id=customer_type_id
        )

        for image in images:
            FaceData.objects.create(customer=customer, image=image)

        # Yeni müşteri eklendikten sonra modeli yeniden eğit (background'da)
        training_thread = threading.Thread(target=retrain_model_async, daemon=True)
        training_thread.start()
        logger.info(f"Yeni müşteri eklendi: {full_name} - Model eğitimi tetiklendi")

    customers = Customer.objects.order_by('-created_at')
    customer_types = CustomerType.objects.all()

    return render(request, 'ControlPanel/customers_page.html', {'customers': customers, 'customer_types': customer_types})



@csrf_exempt
def delete_customer(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        customer_id = data.get('id')
    
        try:
            customer = Customer.objects.get(id=customer_id)
            customer.delete()
            return JsonResponse({'success': True})
        except Customer.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Customer not found'})
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=400)




class CustomerFaceListView(APIView):
    def get(self, request):
        customers = Customer.objects.prefetch_related('face_data').all()
        serializer = CustomerFaceSerializer(customers, many=True, context={'request': request})
        return Response(serializer.data)
    



class AccessLogViewSet(viewsets.ModelViewSet):
    """Geçiş kayıtları API ViewSet"""
    queryset = AccessLog.objects.select_related('customer').all()
    serializer_class = AccessLogSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AccessLogCreateSerializer
        return AccessLogSerializer
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Bugünkü geçişler"""
        today = timezone.now().date()
        logs = self.queryset.filter(entry_time__date=today)
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """İstatistikler"""
        today = timezone.now().date()
        
        stats = {
            'today_total': self.queryset.filter(entry_time__date=today).count(),
            'today_unique': self.queryset.filter(entry_time__date=today).values('customer').distinct().count(),
            'last_hour': self.queryset.filter(entry_time__gte=timezone.now() - timedelta(hours=1)).count(),
            'total': self.queryset.count()
        }
        return Response(stats)


@login_required(login_url='/login/')
def access_logs_view(request):
    """Access logs list with filtering"""
    logs = AccessLog.objects.select_related('customer').all()

    # Filter by customer name
    customer_name = request.GET.get('customer', '').strip()
    if customer_name:
        logs = logs.filter(customer__full_name__icontains=customer_name)

    # Filter by date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if date_from:
        logs = logs.filter(entry_time__date__gte=date_from)
    if date_to:
        logs = logs.filter(entry_time__date__lte=date_to)

    # Filter by minimum confidence
    min_confidence = request.GET.get('min_confidence', '')
    if min_confidence:
        logs = logs.filter(confidence_score__gte=float(min_confidence))

    return render(request, 'ControlPanel/access_logs.html', {'logs': logs})


def access_log_dashboard(request):
    """Geçiş kontrol dashboard'u"""
    today = timezone.now().date()
    
    # Bugünkü kayıtlar
    today_logs = AccessLog.objects.filter(entry_time__date=today).select_related('customer')
    
    # İstatistikler
    stats = {
        'today_total': today_logs.count(),
        'registered_users': Customer.objects.count(),
        'last_hour': AccessLog.objects.filter(
            entry_time__gte=timezone.now() - timedelta(hours=1)
        ).count(),
    }
    
    # En çok giriş yapanlar
    top_customers = AccessLog.objects.filter(
        entry_time__date=today
    ).values(
        'customer__full_name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    context = {
        'logs': today_logs[:50],  # Son 50 kayıt
        'stats': stats,
        'top_customers': top_customers,
    }
    
    return render(request, 'ControlPanel/home.html', context)

