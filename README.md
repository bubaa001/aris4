# Aris 4.0

## 🐳 Docker Setup & Workflow

### First time (requires internet)
```bash
# Build & start everything (web + qcluster)
docker compose up --build -d

# Include ngrok tunnel (optional)
docker compose --profile online up --build -d
```

### Normal usage (works fully offline ✅)
Once the images are built, **you can work completely offline**. The project folder is mounted as a live volume inside the container, so:

1. **Edit any file** (Python, HTML, CSS, JS) — just save
2. **Django auto-reloads** automatically (no rebuild needed)
3. **Refresh your browser** to see changes

```bash
# Start containers (offline-safe, no internet needed)
docker compose start

# Stop containers
docker compose stop

# View logs
docker compose logs web --tail 20
```

### When you need to rebuild
Only rebuild if you **add new Python packages** to `requirements.txt`:

```bash
docker compose up --build -d
```

### Run locally (without Docker)
```bash
python manage.py runserver
```

### Useful URLs
| Service | URL |
|---------|-----|
| Local app | http://localhost:8000 |
| Ngrok tunnel | https://crusader-easing-overlying.ngrok-free.dev |

### Container services
| Service | Description |
|---------|-------------|
| **web** | Django app (port 8000) |
| **qcluster** | Background task queue |
| **ngrok** | Public tunnel (profile: online) |





