FROM python:3.11-slim

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus0 \
    libffi-dev \
    libnacl-dev \
    gcc \
    portaudio19-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create debug directory for audio analysis
RUN mkdir -p /app/debug_audio

EXPOSE 8000

# Default to running the test service, but can be overridden
CMD ["python", "main.py"]