# CLAUDE.md

## Project Overview
Discord voice bot with STT/TTS integration using Docker Compose with 3 services.


**CRITICAL RULES**
- Start each session by reviewing git_log.md
- Always consult github documentation for each module while planning. 
- Test all code after finishing each task before moving on by reading the docker logs. 
- When completing a phase, git commit with detailed comment.

## Development Commands
- `docker-compose up --build` - Start all services (app, STT, TTS)

## Architecture
- **Main App** (port 8000): Discord bot with py-cord[voice] and PyNaCl
- **WhisperLive STT** (port 9090): Speech-to-text WebSocket service
- **Piper TTS** (port 8080): Text-to-speech HTTP service

## Key Files
- `src/bot.py` - Main Discord bot with voice commands
- `src/stt_client.py` - WhisperLive WebSocket client
- `src/tts_client.py` - Piper HTTP client
- `.env` - Contains DISCORD_TOKEN
