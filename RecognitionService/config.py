from pathlib import Path
HOST = "http://127.0.0.1"
PORT = 8000
API_BASE_URL = f"{HOST}:{PORT}/api/"
TIMEOUT = 3 #seconds

BASE_DIR = Path(__file__).parent
CUSTOMER_FACES = "customers/faces/"