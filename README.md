# Face Recognition Based Access Control

An access control system for a gym: a camera at the door recognises members by
face and logs their entry, while a Django control panel manages members, devices
and access records.

Undergraduate capstone project — Computer Engineering.

---

## How it works

The system is two independent services that talk over a REST API.

```
┌─────────────────────────────┐         ┌──────────────────────────────┐
│  RecognitionService         │         │  GYM_Access_Control          │
│  (runs at the door)         │         │  (Django + DRF)              │
│                             │         │                              │
│  CaptureService  ──frames──▶│         │  Customer / FaceData         │
│  (thread + queue)           │         │  AccessPoint / AccessLog     │
│         │                   │         │  CustomBaseUser              │
│         ▼                   │         │                              │
│  RealtimeFaceRecognition    │◀──GET───│  /api/customers/faces/       │
│         │                   │  faces  │                              │
│         ▼                   │         │                              │
│  AccessLogger  ─────────────│──POST──▶│  /api/access-logs/           │
│                             │  entry  │         │                    │
└─────────────────────────────┘         │         ▼                    │
                                        │  Dashboard (who entered)     │
                                        └──────────────────────────────┘
```

1. `ModelTrainer` downloads member photos from the API and builds a face
   encoding model.
2. `CaptureService` reads camera frames on its own thread and feeds a bounded
   queue, so a slow recognition pass never blocks the camera.
3. `RealtimeFaceRecognition` matches each frame against the model and, on a
   confident match, hands the event to `AccessLogger`.
4. `AccessLogger` POSTs the entry — member, confidence score, camera location —
   back to Django, where it appears on the dashboard.

**Model hot-reload:** the recognition loop watches the model file's timestamp
(`_check_and_reload_model`). Retraining after adding a new member takes effect
without restarting the service.

---

## Components

### `RecognitionService/` — the edge service

| File | Responsibility |
|---|---|
| `CaptureService.py` | Threaded camera capture into a frame queue |
| `RecognitionService.py` | Real-time recognition loop, model hot-reload |
| `ModelTrainer.py` | Encoding extraction, training, saving, stats |
| `ClientService.py` | Pulls member face images from the API |
| `LogService.py` | Posts access events back to the API |
| `config.py`, `camera_config.yaml` | API address, camera source, queue size |

### `GYM_Access_Control/` — the control panel

| Model | Purpose |
|---|---|
| `CustomBaseUser` | Email-based auth; `is_app_user` marks service accounts |
| `Customer` / `CustomerType` | Members and membership tiers |
| `FaceData` | Member face images used for training |
| `AccessPoint` | Door devices — Raspberry Pi host, MAC, static IP, heartbeat |
| `AccessLog` | Entry records with confidence score and camera location |
| `Employee` / `EmployeeType` | Staff records |

---

## API

| Method | Path | Used by |
|---|---|---|
| `GET` | `/api/customers/faces/` | Recognition service — fetches training images |
| `GET` `POST` | `/api/access-logs/` | Recognition service — records entries |
| — | `/` | Dashboard |
| — | `/customers/` | Member management |
| — | `/access-logs/` | Entry history |
| — | `/login/` `/logout/` | Authentication |

---

## Stack

| Layer | Technology |
|---|---|
| Control panel | Django 6.0, Django REST Framework |
| Recognition | `face_recognition` (dlib), OpenCV, NumPy |
| Database | SQLite |
| Edge device | Raspberry Pi with camera |

---

## Setup

```bash
git clone git@github.com:melercg/Face-Recognition-Based-Access-Control-Systems.git
cd Face-Recognition-Based-Access-Control-Systems

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> `dlib` compiles from source and needs CMake and a C++ toolchain.
> On Debian/Ubuntu: `sudo apt install cmake build-essential`

**Control panel:**

```bash
cd GYM_Access_Control
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

**Recognition service** — in a second terminal, with the panel running:

```bash
cd RecognitionService
python train_model.py    # builds face_recognition_model.pkl from API images
python app.py            # starts the camera and recognition loop
```

Point `config.py` at the panel's address, and set the camera index in
`camera_config.yaml` (`CameraSource: 0` is the default webcam).

---

## Roadmap

- [ ] Move settings and credentials out of source into environment variables
- [ ] Heartbeat monitoring for access points
- [ ] Liveness detection against photo spoofing
- [ ] Per-device deployment scripts for Raspberry Pi
