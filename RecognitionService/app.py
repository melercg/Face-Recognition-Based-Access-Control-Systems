from CaptureService import CaptureService
from ClientService import RecognizerClient
from ModelTrainer import FaceRecognitionTrainer
from RecognitionService import RealtimeFaceRecognition
from PIL import Image
import numpy as np





def main():

    """capture = CaptureService('./config.yaml')

    capture.start()

    recognition_th = FaceRecognitionService(capture.que)

    recognition_th.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Durduruluyor...")
        capture.stop()
        recognition_th.stop()
        
        capture.join()
        recognition_th.join()"""
    

    """ client = RecognizerClient()
    
    trainer = FaceRecognitionTrainer(client=client)
    
     # Modeli eğit
    print("\n" + "="*60)
    print("FACE RECOGNITION MODEL EĞİTİMİ BAŞLIYOR")
    print("="*60 + "\n")
    
    success_count, total_count = trainer.train_model()
    
    # Modeli kaydet
    if success_count > 0:
        if trainer.save_model():
            print("\n" + "="*60)
            print("✓ MODEL BAŞARIYLA EĞİTİLDİ VE KAYDEDİLDİ!")
            print("="*60)
            print(f"  Başarılı: {success_count}/{total_count}")
            print(f"  Model: {trainer.model_save_path}")
            
            # Model istatistikleri
            stats = trainer.get_model_stats()
            print(f"\n  Toplam Encoding: {stats['total_encodings']}")
            print(f"  Benzersiz Kişi: {stats['unique_persons']}")
            print(f"  Kişiler: {', '.join(stats['persons'])}")
            print("="*60 + "\n")
        else:
            print("\n✗ Model kaydedilemedi!")
    else:
        print("\n✗ Model eğitilemedi - hiç encoding oluşturulamadı!")  """
    
    
    

if __name__ == "__main__":
    try:
        # Gerçek zamanlı yüz tanıma servisi oluştur
        recognition_service = RealtimeFaceRecognition(
            config_path="camera_config.yaml",
            model_path="face_recognition_model.pkl"
        )
        
        # Servisi başlat
        print("\n" + "="*60)
        print("GERÇEK ZAMANLI YÜZ TANIMA SERVİSİ")
        print("="*60)
        print("Çıkmak için 'q' tuşuna basın")
        print("="*60 + "\n")
        
        recognition_service.start(show_window=True)
        
    except Exception as e:
        import traceback
        traceback.print_exc() 


