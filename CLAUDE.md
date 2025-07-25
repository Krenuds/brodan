# CLAUDE.md

## Project Overview
**BRODAN** - Discord voice bot enabling conversational programming for blind and visually impaired users. Natural language interface to Claude Code CLI through voice commands.

## Accessibility Mission 🦾
This project serves blind and visually impaired users who need alternative ways to interact with computers and develop software. The voice interface provides:
- Natural language programming through conversational AI
- Audio-first development workflow replacing visual IDEs  
- Voice-controlled code generation, editing, and project management
- Accessible alternative to traditional screen-reader + IDE workflows

**CRITICAL RULES**
- Start each session by running 'python3 makeLogs.py 10' 
- review the generated latest 3 (of 10) commits at the top of the file.
- Always consult github documentation for each module while planning. 
- Test all code after finishing each task before moving on by reading the docker logs. 
- When completing a phase, git commit with detailed comment.

## Development Commands
- `docker-compose up --build` - Start all services (app, STT, TTS)

## Current Architecture (Stable v1.0) ✅
- **Main App** (port 8000): Discord bot with py-cord[voice] and PyNaCl
- **WhisperLive STT** (port 9090): Speech-to-text WebSocket service  
- **Piper TTS** (port 8080): Text-to-speech HTTP service with Alba British voice
- **Claude Bridge**: Stateless CLI integration for voice-to-code conversion

**Voice Pipeline**: Discord Audio → STT → Claude CLI → TTS → Discord Audio

## Next Generation Architecture (v2.0 Roadmap) 🚀
**Problem**: Current system loses conversation context between voice interactions
**Solution**: Persistent conversational agent with memory and context awareness

### Phase 1: Conversation State Management
- Replace isolated `claude --print` calls with persistent Claude session
- Implement conversation memory and context preservation
- Add intelligent conversation flow management

### Phase 2: Dual Agent Architecture
- **Conversational Agent**: Natural dialogue, explanations, guidance
- **Agentic CLI Agent**: Complex task execution, code generation, file operations
- Smart routing between conversational and action-oriented responses

### Phase 3: Accessibility Enhancements
- Context-aware responses optimized for audio consumption
- Smart response pacing for complex explanations
- Voice feedback for long-running operations
- Conversation state indicators ("Let me think about that...")

## Key Files
- `src/bot.py` - Main Discord bot with voice commands
- `src/claude_bridge.py` - Claude CLI integration (needs v2.0 upgrade)
- `src/stt_client.py` - WhisperLive WebSocket client
- `src/tts_client.py` - Piper HTTP client with Alba voice
- `.env` - Contains DISCORD_TOKEN
