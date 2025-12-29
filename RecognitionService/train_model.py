#!/usr/bin/env python3
"""
Model eğitim scripti
Django'dan subprocess olarak çağrılabilir
"""
import sys
import logging
from ModelTrainer import FaceRecognitionTrainer

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def train():
    """Modeli eğit ve kaydet"""
    logger.info("Model eğitimi başlatılıyor...")

    trainer = FaceRecognitionTrainer(model_save_path="face_recognition_model.pkl")

    successful, total = trainer.train_model()

    if successful > 0:
        trainer.save_model()
        logger.info(f"Model başarıyla eğitildi: {successful}/{total} encoding")
        return True
    else:
        logger.error("Model eğitilemedi: Hiç encoding oluşturulamadı")
        return False


if __name__ == "__main__":
    success = train()
    sys.exit(0 if success else 1)
