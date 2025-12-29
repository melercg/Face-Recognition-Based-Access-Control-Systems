import requests
import re
from collections import deque,ChainMap
import logging
from config import API_BASE_URL, CUSTOMER_FACES, TIMEOUT
from pprint import pprint
from PIL import Image, ImageFilter
from io import BytesIO
from pathlib import Path
import numpy as np
logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class RecognizerClient:

    def __init__(self, base_url = API_BASE_URL, user_output_directories:str = None):
        
        self.base_url = base_url.rstrip("/")

        self.session = requests.Session();
        self.session.headers.update({'Authorization':'Bearer{token}'})

        self.face_config = {
            'thumbnail_size': (512, 512)
        }
        self.io_params = {
            'quality': 80, 
            'optimize': True
        }


    @property
    def customer_faces(self):
        faces_url = f"{self.base_url}/{CUSTOMER_FACES}"
        try: 
            response = self.session.get(faces_url,timeout=TIMEOUT)
            if response.status_code == 200:
                raw_json = response.json()
                user_datas = deque([])

                for person in raw_json:
                    logger.info(f"Processing {person['full_name']} faces")

                    user_fullname = person['full_name']

                    user_id = person['id']
                    face_data =  deque([])
                    

                    for raw_face in person['face_data']:
                        
                        image  = self.download_raw_faces(raw_face['image'])

                        reshaped_image = self.optimize_face_image(image)

                        face_data.appendleft(reshaped_image['data'])

                    user = {
                        'username': re.sub(r"\s+", "", user_fullname, flags=re.UNICODE),
                        'userid': user_id,
                        'faces': face_data
                    }

                    user_datas.append(user)

                return user_datas
                    
                        
                        

            else:
                raise requests.exceptions.HTTPError()

        except requests.RequestException as e:
            logger.error("API Error: API Endpoint didn't return response")
            return 
        
    
    def download_raw_faces(self, data_url:str):
        with self.session.get(data_url, stream=True,timeout=3) as response:

            response.raise_for_status()

            logger.info("Downloading {0}".format(data_url))

            img = Image.open(BytesIO(response.content)).convert('RGB')
            
            return img
        

    def optimize_face_image(self, image_data):

        try:
            

            img = image_data

            img.thumbnail(self.face_config['thumbnail_size'], Image.Resampling.LANCZOS)

            img.filter(ImageFilter.UnsharpMask(radius=2, percent=200, threshold=3))

            img_arr = np.array(img)


            return {
                'data': img_arr,
                'size_kb' : img_arr.nbytes / 1024,
                'dimensions': img.size,
            }


        except Exception as e:
            logger.error(f"Image optimization failed: {e}")
            return None