FROM python:3.11-slim

# Install system dependencies for audio processing and Node.js
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus0 \
    libffi-dev \
    libnacl-dev \
    gcc \
    portaudio19-dev \
    python3-dev \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 18.x (required for Claude Code CLI)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Run the Discord bot
CMD ["python", "-m", "src.bot"]