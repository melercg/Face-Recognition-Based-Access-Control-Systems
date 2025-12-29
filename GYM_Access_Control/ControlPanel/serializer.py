from rest_framework import serializers
from .models import Customer, FaceData, AccessLog

class FaceDataSerializer(serializers.ModelSerializer):

    image = serializers.ImageField(use_url = True)


    class Meta:
        
        model = FaceData
        fields = ['id', 'image', 'uploaded_at']

class CustomerFaceSerializer(serializers.ModelSerializer):
    face_data = FaceDataSerializer(many=True, read_only=True)  # Burada ilişki adı doğru kullanıldı.

    class Meta:
        model = Customer
        fields = ['id', 'full_name', 'face_data']
        
class AccessLogSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    
    class Meta:
        model = AccessLog
        fields = ['id', 'customer', 'customer_name', 'entry_time', 
                  'confidence_score', 'camera_location', 'snapshot']
        read_only_fields = ['entry_time']


class AccessLogCreateSerializer(serializers.Serializer):
    """Geçiş kaydı oluşturma için özel serializer"""
    customer_id = serializers.IntegerField()
    confidence_score = serializers.FloatField(min_value=0, max_value=1)
    camera_location = serializers.CharField(max_length=100, required=False, default="Ana Giriş")
    snapshot_base64 = serializers.CharField(required=False, allow_blank=True)
    
    def create(self, validated_data):
        from django.core.files.base import ContentFile
        import base64
        
        customer_id = validated_data.pop('customer_id')
        snapshot_base64 = validated_data.pop('snapshot_base64', None)
        
        try:
            customer = Customer.objects.get(id=customer_id, is_active=True)
        except Customer.DoesNotExist:
            raise serializers.ValidationError("Müşteri bulunamadı veya aktif değil")
        
        access_log = AccessLog.objects.create(
            customer=customer,
            **validated_data
        )
        
        # Snapshot varsa kaydet
        if snapshot_base64:
            try:
                image_data = base64.b64decode(snapshot_base64)
                access_log.snapshot.save(
                    f"access_{customer.id}_{access_log.entry_time.timestamp()}.jpg",
                    ContentFile(image_data),
                    save=True
                )
            except Exception as e:
                pass  # Snapshot kaydedilemese bile devam et
        
        return access_log
