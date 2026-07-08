# aris4.0

Django learning platform with XP tiers, quizzes, archive, library, and offline-first sync.

## Setup

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # optional
```

## Run (local — no internet needed)

```powershell
python manage.py runserver
# → http://127.0.0.1:8000/

python manage.py qcluster          # background tasks (terminal 2)
```

## Run with ngrok (public URL — internet required)

```powershell
# Terminal 1
python manage.py runserver --ngrok

# Terminal 2
ngrok http --url=crusader-easing-overlying.ngrok-free.dev 80

# Terminal 3
python manage.py qcluster
```

Site: https://crusader-easing-overlying.ngrok-free.dev

## Admin

```
http://127.0.0.1:8000/admin-dashboard/
```
