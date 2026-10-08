FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for MoviePy and mysql client
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Fix ImageMagick policy for MoviePy text rendering
RUN sed -i 's/none/read,write/g' /etc/ImageMagick-6/policy.xml || true

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure logs directory exists
RUN mkdir -p logs

CMD ["python", "worker.py"]

