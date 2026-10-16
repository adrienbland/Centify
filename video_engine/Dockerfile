FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for MoviePy, FFmpeg and fonts for subtitles
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Fix ImageMagick policy for MoviePy text rendering
RUN sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml || true

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .

# Ensure logs and medias directories exist
RUN mkdir -p logs /app/medias/library /app/medias/renders

CMD ["python", "worker.py"]
