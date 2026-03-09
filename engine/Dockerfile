FROM python:3.12-slim

WORKDIR /app

# System dependencies for ffmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Create directories for media processing
RUN mkdir -p /app/media/videos /app/media/images /app/media/audio

EXPOSE 8300

CMD ["python", "main.py"]
