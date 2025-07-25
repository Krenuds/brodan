# Claude Code Integration Module

## Project Overview
Voice-enabled Claude Code integration for Discord voice bot, enabling direct voice conversations with Claude Code through Discord voice channels.

## Current System Architecture

### Existing Services
- **Discord Voice Bot** (port 8000): Multi-user voice capture from Discord channels
- **WhisperLive STT** (port 9090): Real-time speech-to-text WebSocket service
- **Piper TTS** (port 8080): Text-to-speech HTTP service

### Key Components
- `src/stt_client.py`: Discord audio processing with VAD, resampling, and segment tracking
- `src/audio_processor.py`: Discord voice channel audio sink with energy-based VAD
- `src/bot.py`: Discord bot with auto-join and transcription monitoring

## Integration Challenge

**Goal**: Enable voice conversations with Claude Code directly from Discord voice channels.

**Problem**: Voice-mode MCP requires OpenAI-compatible STT API, but our WhisperLive uses WebSocket protocol.

**Solution**: Replace WhisperLive with whisper.cpp server + create Discord audio bridge for direct integration.

## Selected Implementation: Direct Audio Integration (Option B)

### Architecture
```
Discord Voice → Audio Bridge → whisper.cpp (OpenAI API) → Voice-Mode MCP → Claude Code
```

### Implementation Strategy

#### Phase 1: Replace WhisperLive with whisper.cpp
1. **Update Docker Compose** (`docker-compose.yml`):
   - Replace WhisperLive service with whisper.cpp server
   - Expose OpenAI-compatible API on port 9090
   - Maintain model persistence via volumes

2. **Update STT Client** (`src/stt_client.py`):
   - Replace WebSocket client with HTTP client for whisper.cpp
   - Implement OpenAI API format requests
   - Maintain existing audio processing capabilities

#### Phase 2: Create Discord Audio Bridge
1. **Discord Audio Bridge** (`src/discord_audio_bridge.py`):
   - FastAPI server on port 9091
   - OpenAI-compatible `/v1/audio/transcriptions` endpoint
   - Direct integration with Discord AudioSink
   - Real-time audio streaming from Discord channels

2. **Audio Processor Integration** (`src/audio_processor.py`):
   - Stream Discord audio to both whisper.cpp and audio bridge
   - Maintain VAD capabilities for voice activity detection
   - Support multiple audio formats for voice-mode compatibility

#### Phase 3: Voice-Mode MCP Integration
1. **Configure Voice-Mode**:
   ```bash
   claude mcp add voice-mode --env VOICEMODE_STT_BASE_URL=http://localhost:9091/v1
   export VOICEMODE_TTS_BASE_URL=http://localhost:8080/v1
   export OPENAI_API_KEY=dummy  # Not needed for local STT
   ```

2. **Enhanced Integration**:
   - TTS responses played back in Discord voice channels
   - Multi-user voice command handling
   - Context-aware conversations per Discord user

## Technical Implementation

### Dependencies
```txt
# Add to requirements.txt
fastapi>=0.104.0
uvicorn>=0.24.0
sse-starlette>=1.6.5
httpx>=0.25.0  # For whisper.cpp HTTP client
```

### Environment Configuration
```bash
# Discord Bot
DISCORD_TOKEN=your_discord_token

# Claude Code Voice Integration
VOICEMODE_STT_BASE_URL=http://localhost:9091/v1
VOICEMODE_TTS_BASE_URL=http://localhost:8080/v1
VOICEMODE_DEBUG=true
OPENAI_API_KEY=dummy  # Not needed for local STT
CLAUDE_CODE_VOICE_ENABLED=true

# Discord Audio Bridge
DISCORD_AUDIO_BRIDGE_PORT=9091
WHISPER_CPP_BASE_URL=http://localhost:9090/v1
```

### Docker Compose Updates
```yaml
services:
  app:
    ports:
      - "8000:8000"
      - "9091:9091"  # Discord audio bridge
    environment:
      - VOICEMODE_STT_BASE_URL=http://localhost:9091/v1
      - VOICEMODE_TTS_BASE_URL=http://localhost:8080/v1
      - WHISPER_CPP_BASE_URL=http://whisper-stt:9090/v1

  whisper-stt:
    image: ghcr.io/ggerganov/whisper.cpp:server
    ports:
      - "9090:9090"
    volumes:
      - whisper-models:/models
    command: ["--host", "0.0.0.0", "--port", "9090", "--model", "/models/ggml-base.en.bin"]

  piper-tts:
    build: ./services/piper-http
    ports:
      - "8080:8080"
    volumes:
      - piper-models:/models
```

## Implementation Files

### New Files
- `src/discord_audio_bridge.py` - OpenAI-compatible audio bridge for Discord
- `tests/test_voice_integration.py` - Automated test suite
- `.env.example` - Environment variable documentation

### Modified Files
- `src/stt_client.py` - Replace WebSocket with HTTP client for whisper.cpp
- `src/audio_processor.py` - Add audio bridge integration
- `docker-compose.yml` - Replace WhisperLive with whisper.cpp
- `requirements.txt` - Add FastAPI and HTTP client dependencies
- `CLAUDE.md` - Update with voice integration commands

## Success Criteria

### Phase 1 Completion
- [ ] whisper.cpp server operational with OpenAI-compatible API
- [ ] STT client successfully connects to whisper.cpp HTTP API
- [ ] No regression in existing Discord voice transcription
- [ ] Docker logs show clean whisper.cpp integration

### Phase 2 Completion
- [ ] Discord audio bridge operational on port 9091
- [ ] OpenAI-compatible STT endpoints responding correctly
- [ ] Real-time Discord audio streaming to bridge
- [ ] Audio format conversions working properly

### Phase 3 Completion
- [ ] Voice-mode MCP connects to Discord audio bridge
- [ ] End-to-end: Discord voice → Claude Code response
- [ ] TTS responses play in Discord voice channels
- [ ] Multi-user voice commands work without interference
- [ ] Transcription latency < 2 seconds

### Integration Tests
- [ ] Automated test suite passes with >90% coverage
- [ ] Performance benchmarks meet latency requirements
- [ ] Docker log validation shows error-free operation
- [ ] End-to-end voice conversation workflow functional

## Testing Strategy

### Development Testing
1. **Docker Services Validation**:
   ```bash
   docker-compose up --build
   docker-compose logs -f app         # Monitor Discord bot
   docker-compose logs -f whisper-stt # Monitor whisper.cpp
   docker-compose logs -f piper-tts   # Monitor TTS service
   ```

2. **API Endpoint Testing**:
   ```bash
   # Test whisper.cpp API
   curl -X POST http://localhost:9090/v1/audio/transcriptions \
     -H "Content-Type: multipart/form-data" \
     -F "file=@test_audio.wav" \
     -F "model=whisper-1"

   # Test Discord audio bridge
   curl http://localhost:9091/health
   curl http://localhost:9091/v1/audio/transcriptions
   ```

3. **Voice-Mode Integration**:
   ```bash
   # Check MCP server status
   claude mcp status voice-mode
   
   # Start voice conversation
   claude converse
   ```

### Performance Benchmarks
- **End-to-End Latency**: < 2 seconds (Discord voice → Claude Code response)
- **STT Processing**: < 1 second for typical voice segments
- **Audio Bridge Latency**: < 100ms for audio forwarding
- **Memory Usage**: < 200MB additional for bridge service

## Development Commands

### Setup Voice Integration
```bash
# Install voice-mode MCP
claude mcp add voice-mode \
  --env VOICEMODE_STT_BASE_URL=http://localhost:9091/v1 \
  --env VOICEMODE_TTS_BASE_URL=http://localhost:8080/v1 \
  --env OPENAI_API_KEY=dummy

# Start integrated system
docker-compose up --build

# Start voice conversation
claude converse
```

### Debug Commands
```bash
# Test whisper.cpp health
curl http://localhost:9090/health

# Test Discord audio bridge
curl http://localhost:9091/health
curl http://localhost:9091/v1/stream

# Monitor transcription logs
docker-compose logs -f whisper-stt

# Check voice-mode status
claude mcp list
claude mcp status voice-mode
```

## Implementation Advantages

### Direct Integration Benefits
- **Reduced Latency**: Eliminates WebSocket → HTTP conversion overhead
- **Simplified Architecture**: Native OpenAI API compatibility
- **Better Performance**: whisper.cpp optimized for production use
- **Seamless Voice-Mode Integration**: No protocol conversion needed

### Maintained Capabilities
- **Discord-Specific Features**: Multi-user audio, VAD, resampling
- **Real-Time Processing**: Low-latency voice activity detection
- **Robust Audio Handling**: Energy-based VAD and segment tracking
- **Fallback Safety**: Graceful degradation if services fail

## Future Enhancements

### Advanced Voice Features
- **Speaker Recognition**: Identify and tag different Discord users in conversations
- **Context Persistence**: Remember conversation history per Discord user
- **Custom Voice Commands**: Project-specific shortcuts and macros
- **Multi-Language Support**: Dynamic language switching via voice

### Claude Code Integration
- **Visual Context**: Screenshot integration for debugging assistance
- **Git Workflow**: Voice-driven commit, push, and PR creation
- **Real-Time Collaboration**: Shared Claude Code sessions with multiple developers
- **Custom Tools**: Discord-aware MCP tools for voice-driven development

---

**Note**: This implementation replaces WhisperLive with whisper.cpp for better voice-mode MCP compatibility while preserving all Discord-specific voice capture capabilities through the custom audio bridge architecture.