import face_recognition
import numpy as np
import pickle
import logging
from typing import List, Tuple, Optional
from pathlib import Path
from ClientService import RecognizerClient

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class FaceRecognitionTrainer:
    """RecognizerClient kullanarak yüz tanıma modeli eğiten sınıf"""
    
    def __init__(self, client: RecognizerClient = None, model_save_path: str = "face_recognition_model.pkl"):
        """
        Args:
            client: RecognizerClient instance (None ise yeni oluşturulur)
            model_save_path: Eğitilen modelin kaydedileceği dosya yolu
        """
        self.client = client if client else RecognizerClient()
        self.model_save_path = Path(model_save_path)
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        
    def extract_face_encoding(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Görüntüden yüz encoding'i çıkarır"""
        try:
            # Görüntüdeki yüzlerin konumlarını bul
            face_locations = face_recognition.face_locations(image, model='hog')
            
            if not face_locations:
                logger.warning("Görüntüde yüz bulunamadı")
                return None
            
            # İlk yüzün encoding'ini al
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            if face_encodings:
                return face_encodings[0]
            return None
        except Exception as e:
            logger.warning(f"Face encoding çıkarılamadı: {e}")
            return None
    
    def train_model(self) -> Tuple[int, int]:
        """Modeli eğitir ve başarı oranını döndürür"""
        logger.info("API'dan yüz verileri çekiliyor...")
        
        # RecognizerClient kullanarak verileri çek
        customers_data = self.client.customer_faces
        
        if not customers_data:
            logger.error("API'dan veri çekilemedi")
            return 0, 0
        
        total_images = 0
        successful_encodings = 0
        
        # Her müşteri için
        for customer in customers_data:
            username = customer['username']
            user_id = customer['userid']
            faces = customer['faces']
            
            logger.info(f"İşleniyor: {username} (ID: {user_id}) - {len(faces)} görüntü")
            
            # Her yüz görüntüsü için
            for face_image in faces:
                total_images += 1
                
                # Face encoding çıkar (image zaten numpy array olarak geliyor)
                encoding = self.extract_face_encoding(face_image)
                
                if encoding is not None:
                    self.known_face_encodings.append(encoding)
                    self.known_face_names.append(username)
                    self.known_face_ids.append(user_id)
                    successful_encodings += 1
                    logger.info(f"✓ Encoding eklendi: {username} (ID: {user_id})")
        
        logger.info(f"\n{'='*50}")
        logger.info(f"Eğitim tamamlandı: {successful_encodings}/{total_images} görüntü başarılı")
        logger.info(f"{'='*50}\n")
        
        return successful_encodings, total_images
    
    def save_model(self) -> bool:
        """Eğitilen modeli dosyaya kaydeder"""
        if not self.known_face_encodings:
            logger.warning("Kaydedilecek encoding bulunamadı")
            return False
        
        model_data = {
            'encodings': self.known_face_encodings,
            'names': self.known_face_names,
            'ids': self.known_face_ids,
            'total_faces': len(self.known_face_encodings)
        }
        
        try:
            with open(self.model_save_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"Model kaydedildi: {self.model_save_path}")
            logger.info(f"Toplam encoding sayısı: {len(self.known_face_encodings)}")
            return True
        except Exception as e:
            logger.error(f"Model kaydedilemedi: {e}")
            return False
    
    def load_model(self) -> bool:
        """Kaydedilmiş modeli yükler"""
        if not self.model_save_path.exists():
            logger.error(f"Model dosyası bulunamadı: {self.model_save_path}")
            return False
        
        try:
            with open(self.model_save_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.known_face_encodings = model_data['encodings']
            self.known_face_names = model_data['names']
            self.known_face_ids = model_data.get('ids', [])
            
            logger.info(f"Model yüklendi: {len(self.known_face_encodings)} encoding")
            return True
        except Exception as e:
            logger.error(f"Model yüklenemedi: {e}")
            return False
    
    def recognize_face(self, image_path: str, tolerance: float = 0.6) -> List[dict]:
        """
        Verilen görüntüdeki yüzleri tanır
        
        Args:
            image_path: Tanınacak görüntünün yolu
            tolerance: Eşleştirme toleransı (düşük = daha katı)
            
        Returns:
            Tanınan yüzlerin listesi [{'name': str, 'user_id': int, 'confidence': float}]
        """
        if not self.known_face_encodings:
            logger.error("Model yüklenmemiş veya eğitilmemiş")
            return []
        
        # Görüntüyü yükle
        unknown_image = face_recognition.load_image_file(image_path)
        
        # Yüz konumlarını ve encoding'lerini bul
        face_locations = face_recognition.face_locations(unknown_image)
        face_encodings = face_recognition.face_encodings(unknown_image, face_locations)
        
        logger.info(f"{len(face_encodings)} yüz tespit edildi")
        
        recognized_faces = []
        
        for face_encoding in face_encodings:
            # Bilinen yüzlerle karşılaştır
            matches = face_recognition.compare_faces(
                self.known_face_encodings, 
                face_encoding, 
                tolerance=tolerance
            )
            
            name = "Bilinmeyen"
            user_id = None
            confidence = 0.0
            
            # Eşleşme varsa en yakın olanı bul
            if True in matches:
                face_distances = face_recognition.face_distance(
                    self.known_face_encodings, 
                    face_encoding
                )
                best_match_index = np.argmin(face_distances)
                
                if matches[best_match_index]:
                    name = self.known_face_names[best_match_index]
                    user_id = self.known_face_ids[best_match_index]
                    # Güven skoru (0-1 arası, 1 = en yüksek güven)
                    confidence = 1 - face_distances[best_match_index]
            
            recognized_faces.append({
                'name': name,
                'user_id': user_id,
                'confidence': round(confidence, 3)
            })
        
        return recognized_faces
    
    def get_model_stats(self) -> dict:
        """Model istatistiklerini döndürür"""
        if not self.known_face_encodings:
            return {'status': 'Model yüklenmemiş'}
        
        unique_names = set(self.known_face_names)
        
        return {
            'total_encodings': len(self.known_face_encodings),
            'unique_persons': len(unique_names),
            'persons': list(unique_names),
            'model_path': str(self.model_save_path)
        }