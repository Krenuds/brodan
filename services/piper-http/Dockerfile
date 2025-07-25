FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libsndfile1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    piper-tts \
    fastapi \
    uvicorn \
    numpy

WORKDIR /app

# Create models directory and download alba voice
RUN mkdir -p /models && cd /models && \
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/alba/medium/en_GB-alba-medium.onnx && \
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/alba/medium/en_GB-alba-medium.onnx.json

COPY server.py .

EXPOSE 8080

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]