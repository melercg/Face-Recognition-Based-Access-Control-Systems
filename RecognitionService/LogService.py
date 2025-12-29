import requests
import base64
import cv2
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AccessLogger:
    """Geçiş kayıtlarını server'a gönderen servis"""
    
    def __init__(self, api_base_url: str, api_token: str = None):
        self.api_base_url = api_base_url.rstrip('/')
        self.api_url = f"{self.api_base_url}/api/access-logs/"
        
        self.session = requests.Session()
        if api_token:
            self.session.headers.update({'Authorization': f'Bearer {api_token}'})
        
    def log_access(self, customer_id: int, confidence: float, 
                   frame: 'np.ndarray' = None, camera_location: str = "Ana Giriş") -> bool:
        """
        Geçiş kaydını server'a gönder
        
        Args:
            customer_id: Müşteri ID
            confidence: Tanınma güven skoru
            frame: Görüntü frame'i (opsiyonel)
            camera_location: Kamera konumu
            
        Returns:
            bool: Başarılı ise True
        """
        try:
            payload = {
                'customer_id': customer_id,
                'confidence_score': confidence,
                'camera_location': camera_location
            }
            
            # Frame varsa base64'e çevir
            if frame is not None:
                try:
                    _, buffer = cv2.imencode('.jpg', frame)
                    snapshot_base64 = base64.b64encode(buffer).decode('utf-8')
                    payload['snapshot_base64'] = snapshot_base64
                except Exception as e:
                    logger.warning(f"Snapshot encode edilemedi: {e}")
            
            response = self.session.post(self.api_url, json=payload, timeout=5)
            
            if response.status_code == 201:
                logger.info(f"✓ Geçiş kaydı oluşturuldu: Customer ID {customer_id}")
                return True
            else:
                logger.error(f"✗ Geçiş kaydı oluşturulamadı: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ API isteği başarısız: {e}")
            return False
    
    def get_today_logs(self):
        """Bugünkü kayıtları getir"""
        try:
            response = self.session.get(f"{self.api_url}today/", timeout=5)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Kayıtlar getirilemedi: {e}")
            return []
    
    def get_stats(self):
        """İstatistikleri getir"""
        try:
            response = self.session.get(f"{self.api_url}stats/", timeout=5)
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"İstatistikler getirilemedi: {e}")
            return {}
