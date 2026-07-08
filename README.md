# aris4.0

Django learning platform with XP tiers, quizzes, archive, library, and offline-first sync.

## Quick Start (Docker)

```bash
# Online mode (ngrok public URL)
docker compose up

# Offline mode (local only, no internet needed)
docker compose -f docker-compose.offline.yml up
```

Open http://localhost:8000

## Setup (without Docker)

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # optional
```

## Run (local)

```powershell
python manage.py runserver            # → http://127.0.0.1:8000/
python manage.py qcluster             # background tasks
```

## Run with ngrok

```powershell
python manage.py runserver --ngrok    # terminal 1 (requires --ngrok flag)
ngrok http --url=crusader-easing-overlying.ngrok-free.dev 80  # terminal 2
python manage.py qcluster             # terminal 3
```

Site: https://crusader-easing-overlying.ngrok-free.dev
