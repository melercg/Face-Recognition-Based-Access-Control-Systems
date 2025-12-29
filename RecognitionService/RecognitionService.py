import cv2
import face_recognition
import numpy as np
import logging
import time
import os
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from CaptureService import CaptureService
from ModelTrainer import FaceRecognitionTrainer
from LogService import AccessLogger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class RealtimeFaceRecognition:
    """Gerçek zamanlı yüz tanıma servisi"""
    
    def __init__(self, config_path: str, model_path: str = "face_recognition_model.pkl"):
        """
        Args:
            config_path: CaptureService config dosyası yolu
            model_path: Eğitilmiş model dosyası yolu
        """
        # CaptureService'i başlat
        self.capture_service = CaptureService(config_path)
        
        # Face Recognition Trainer'ı yükle
        self.model_path = Path(model_path)
        self.trainer = FaceRecognitionTrainer(model_save_path=model_path)

        if not self.trainer.load_model():
            raise RuntimeError("Model yüklenemedi! Önce modeli eğitin.")

        # Model hot reload için son değişiklik zamanını tut
        self.last_model_mtime = self._get_model_mtime()
        self.model_check_interval = 30  # Her 30 saniyede bir kontrol et
        self.last_model_check = time.time()

        self.access_logger = AccessLogger("http://127.0.0.1:8000")

        # Tanıma ayarları
        self.recognition_config = {
            'tolerance': 0.6,  # Tanıma hassasiyeti
            'process_every_n_frames': 2,  # Her N frame'de bir işle (performans için)
            'min_confidence': 0.5,  # Minimum güven skoru
            'greeting_cooldown': 5,  # Aynı kişiye kaç saniyede bir selam ver
            'api_cooldown': 300  # Aynı kişi için API'ye kaç saniyede bir istek at (5 dakika)
        }

        # Son selamlama zamanlarını tut
        self.last_greeting_time = {}

        # Son API çağrısı zamanlarını tut (user_id bazlı)
        self.last_api_call_time = {}
        
        # İstatistikler
        self.stats = {
            'total_frames': 0,
            'processed_frames': 0,
            'faces_detected': 0,
            'faces_recognized': 0
        }
        
        self.running = False

    def _get_model_mtime(self) -> float:
        """Model dosyasının son değişiklik zamanını döndür"""
        try:
            if self.model_path.exists():
                return os.path.getmtime(self.model_path)
        except Exception:
            pass
        return 0

    def _check_and_reload_model(self):
        """Model dosyası değiştiyse yeniden yükle"""
        current_time = time.time()

        # Belirli aralıklarla kontrol et
        if current_time - self.last_model_check < self.model_check_interval:
            return

        self.last_model_check = current_time
        current_mtime = self._get_model_mtime()

        if current_mtime > self.last_model_mtime:
            logger.info("Model dosyası değişti, yeniden yükleniyor...")

            if self.trainer.load_model():
                self.last_model_mtime = current_mtime
                logger.info(f"Model yeniden yüklendi: {len(self.trainer.known_face_encodings)} encoding")

                # Yeni kullanıcılar için cooldown'ları temizle
                self.last_greeting_time.clear()
                self.last_api_call_time.clear()
            else:
                logger.error("Model yeniden yüklenemedi!")

    def greet_person(self, name: str, user_id: int, confidence: float):
        """Kişiye selamlama mesajı göster"""
        current_time = datetime.now()

        # Selamlama cooldown kontrolü
        if name in self.last_greeting_time:
            time_diff = current_time - self.last_greeting_time[name]
            if time_diff < timedelta(seconds=self.recognition_config['greeting_cooldown']):
                return  # Çok erken, selamlama

        # Selamlama mesajı
        print("\n" + "="*60)
        print(f"🎉 HOŞGELDİN {name.upper()}!")
        print(f"👤 User ID: {user_id}")
        print(f"✓ Güven: %{confidence*100:.1f}")
        print(f"⏰ Zaman: {current_time.strftime('%H:%M:%S')}")
        print("="*60 + "\n")

        logger.info(f"Kişi tanındı: {name} (ID: {user_id}, Güven: %{confidence*100:.1f})")

        # Son selamlama zamanını güncelle
        self.last_greeting_time[name] = current_time
        self.stats['faces_recognized'] += 1

        # API cooldown kontrolü (5 dakika)
        should_call_api = True
        if user_id in self.last_api_call_time:
            api_time_diff = current_time - self.last_api_call_time[user_id]
            if api_time_diff < timedelta(seconds=self.recognition_config['api_cooldown']):
                should_call_api = False
                logger.debug(f"API cooldown aktif: {name} (ID: {user_id}) - Kalan süre: {self.recognition_config['api_cooldown'] - api_time_diff.total_seconds():.0f} saniye")

        if should_call_api:
            self.access_logger.log_access(
                customer_id=user_id,
                confidence=confidence,
                camera_location="Ana Giriş Kamera 1"
            )
            self.last_api_call_time[user_id] = current_time
            logger.info(f"API'ye erişim kaydı gönderildi: {name} (ID: {user_id})")
    
    def process_frame(self, frame: np.ndarray):
        """Frame'i işle ve yüzleri tanı"""
        # Frame zaten CaptureService'de 0.5x küçültüldü, tekrar küçültmeye gerek yok
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Yüz konumlarını bul (number_of_times_to_upsample=1 daha hızlı)
        face_locations = face_recognition.face_locations(rgb_frame, model='hog', number_of_times_to_upsample=1)

        if not face_locations:
            return frame, []

        self.stats['faces_detected'] += len(face_locations)

        # Yüz encoding'lerini çıkar
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        recognized_faces = []

        # Her yüz için
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):

            # Bilinen yüzlerle karşılaştır
            matches = face_recognition.compare_faces(
                self.trainer.known_face_encodings,
                face_encoding,
                tolerance=self.recognition_config['tolerance']
            )

            name = "Bilinmeyen"
            user_id = None
            confidence = 0.0

            # Eşleşme varsa en yakın olanı bul
            if True in matches:
                face_distances = face_recognition.face_distance(
                    self.trainer.known_face_encodings,
                    face_encoding
                )
                best_match_index = np.argmin(face_distances)

                if matches[best_match_index]:
                    confidence = 1 - face_distances[best_match_index]

                    # Minimum güven kontrolü
                    if confidence >= self.recognition_config['min_confidence']:
                        name = self.trainer.known_face_names[best_match_index]
                        user_id = self.trainer.known_face_ids[best_match_index]

                        # Kişiye selamla
                        self.greet_person(name, user_id, confidence)

            recognized_faces.append({
                'name': name,
                'user_id': user_id,
                'confidence': confidence,
                'location': (top, right, bottom, left)
            })

            # Yüzün etrafına kutu çiz
            color = (0, 255, 0) if name != "Bilinmeyen" else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            # İsim ve güven skorunu yaz
            label = f"{name}"
            if confidence > 0:
                label += f" (%{confidence*100:.0f})"

            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, label, (left + 6, bottom - 6),
                       cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

        return frame, recognized_faces
    
    def start(self, show_window: bool = True):
        """Gerçek zamanlı tanımayı başlat"""
        self.running = True
        self.capture_service.start()
        
        logger.info("Gerçek zamanlı yüz tanıma başlatıldı")
        logger.info(f"Model: {len(self.trainer.known_face_encodings)} encoding yüklendi")
        logger.info(f"Tanıma toleransı: {self.recognition_config['tolerance']}")
        logger.info(f"Minimum güven: {self.recognition_config['min_confidence']}")
        
        frame_count = 0
        fps_start_time = time.time()
        fps = 0
        
        try:
            while self.running:
                # Model değişikliği kontrolü (hot reload)
                self._check_and_reload_model()

                # Kuyruktan frame al
                if not self.capture_service.que.empty():
                    frame = self.capture_service.que.get()
                    self.stats['total_frames'] += 1
                    frame_count += 1
                    
                    # FPS hesapla
                    if frame_count % 30 == 0:
                        fps_end_time = time.time()
                        fps = 30 / (fps_end_time - fps_start_time)
                        fps_start_time = fps_end_time
                    
                    # Her N frame'de bir işle (performans optimizasyonu)
                    if self.stats['total_frames'] % self.recognition_config['process_every_n_frames'] == 0:
                        processed_frame, recognized_faces = self.process_frame(frame)
                        self.stats['processed_frames'] += 1
                    else:
                        processed_frame = frame
                    
                    # FPS bilgisini frame'e yaz
                    cv2.putText(processed_frame, f"FPS: {fps:.1f}", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # Pencere göster
                    if show_window:
                        cv2.imshow('Face Recognition', processed_frame)
                        
                        # 'q' tuşu ile çıkış
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            logger.info("Kullanıcı çıkış yaptı")
                            break
                else:
                    time.sleep(0.01)
                    
        except KeyboardInterrupt:
            logger.info("Program KeyboardInterrupt ile durduruldu")
        finally:
            self.stop()
    
    def stop(self):
        """Servisi durdur"""
        self.running = False
        self.capture_service.stop()
        cv2.destroyAllWindows()
        
        # İstatistikleri göster
        print("\n" + "="*60)
        print("FACE RECOGNITION İSTATİSTİKLERİ")
        print("="*60)
        print(f"Toplam Frame: {self.stats['total_frames']}")
        print(f"İşlenen Frame: {self.stats['processed_frames']}")
        print(f"Tespit Edilen Yüz: {self.stats['faces_detected']}")
        print(f"Tanınan Yüz: {self.stats['faces_recognized']}")
        print("="*60 + "\n")
        
        logger.info("Face Recognition servisi durduruldu")

