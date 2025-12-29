import cv2
import threading
import queue
import time
import numpy as np
import logging
import yaml

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class CaptureService(threading.Thread):
    def __init__(self, config_path):
        super().__init__()

        with open(config_path, 'r') as config_specs:
        
            self.config = yaml.safe_load(config_specs)

        
        self.capture = cv2.VideoCapture(self.config['CameraSource'])

        if not self.capture.isOpened() :
            logger.error("Camera connection is lost")
            raise RuntimeError("Camera connection is lost")
        

        self.que = queue.Queue(maxsize=self.config['QueueSize'])

        self.thread_start = False


    def run(self):

        last_processes = 0

        self.thread_start = True

        logger.info("Capture service is starting")

        while self.thread_start:


            if not self.que.full():

                success, frame = self.capture.read()

                if not success:

                    logging.error("Couldn't captured frame from camera")

                    

                    break

                small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)


                self.que.put(small_frame)

            
            else:
                time.sleep(0.01)


    def stop(self):
        self.thread_start = False
        self.capture.release()
