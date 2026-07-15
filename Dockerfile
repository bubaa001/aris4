FROM python:3.14-slim

WORKDIR /app

# Install system dependencies + ngrok
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl unzip \
    && curl -sSL https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.zip -o /tmp/ngrok.zip \
    && unzip /tmp/ngrok.zip -d /usr/local/bin \
    && rm /tmp/ngrok.zip \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create media directory for file uploads
RUN mkdir -p media

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
