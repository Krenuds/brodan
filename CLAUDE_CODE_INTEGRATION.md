# Claude Code Integration Module

## Project Overview
Voice-enabled Claude Code integration for Discord voice bot, bridging Discord STT transcription pipeline to Claude Code system agent for conversational coding.

## Current System Architecture

### Existing Services
- **Discord Voice Bot** (port 8000): Multi-user voice capture from Discord channels
- **WhisperLive STT** (port 9090): Real-time speech-to-text WebSocket service
- **Piper TTS** (port 8080): Text-to-speech HTTP service

### Key Components
- `src/stt_client.py` (363 lines): Specialized Discord audio processing with VAD, resampling, and segment tracking
- `src/audio_processor.py`: Discord voice channel audio sink with energy-based VAD
- `src/bot.py`: Discord bot with auto-join and transcription monitoring

## Integration Challenge

**Goal**: Pipe Discord voice transcriptions into Claude Code for conversational system agent interaction.

**Problem**: Voice-mode MCP provides generic microphone → Claude Code integration but cannot capture from Discord voice channels or handle multi-user audio streams.

**Solution**: Hybrid approach preserving Discord voice capture while adding Claude Code integration.

## Integration Architecture Options

### Option A: Named Pipe Bridge (Recommended)
```
Discord Voice → STT Client → Named Pipe → Voice-Mode MCP → Claude Code
```

**Implementation:**
- Modify `src/stt_client.py` to write transcriptions to `/tmp/discord_stt_pipe`
- Configure voice-mode to read from named pipe instead of microphone
- Minimal changes to existing codebase

**Pros:** 
- Preserves all Discord-specific functionality
- Simple Unix IPC mechanism
- No additional dependencies

**Cons:**
- Platform-specific (Unix/Linux only)
- Requires voice-mode modification for pipe input

### Option B: HTTP API Bridge
```
Discord Voice → STT Client → HTTP Server → Voice-Mode MCP → Claude Code
```

**Implementation:**
- Add HTTP server to `src/stt_client.py` mimicking OpenAI STT API
- Configure voice-mode: `VOICEMODE_STT_BASE_URL="http://localhost:9091/v1"`
- RESTful interface for transcription streaming

**Pros:**
- Cross-platform compatibility
- Standard HTTP/REST interface
- Works with existing voice-mode configuration

**Cons:**
- Additional HTTP server complexity
- Network overhead for local communication

### Option C: Custom MCP Server
```
Discord Voice → STT Client → Custom MCP Server → Claude Code
```

**Implementation:**
- Build dedicated MCP server connecting to Discord STT pipeline
- Direct integration with Claude Code via MCP protocol
- Custom tools for Discord-specific voice management

**Pros:**
- Full control over integration
- Native MCP protocol support
- Discord-aware voice commands

**Cons:**
- Most development effort
- Custom MCP server maintenance

## Recommended Implementation Strategy

### Phase 1: HTTP API Bridge (Quick Win)
1. **Extend STT Client** (`src/stt_client.py`):
   - Add FastAPI HTTP server on port 9091
   - Implement OpenAI-compatible `/v1/audio/transcriptions` endpoint
   - Stream real-time transcriptions via Server-Sent Events

2. **Install Voice-Mode MCP**:
   ```bash
   claude mcp add voice-mode --env OPENAI_API_KEY=dummy
   export VOICEMODE_STT_BASE_URL="http://localhost:9091/v1"
   export VOICEMODE_TTS_BASE_URL="http://localhost:8080/v1"
   ```

3. **Test Integration**:
   - Discord voice → STT → HTTP bridge → Claude Code
   - Verify transcription accuracy and latency

### Phase 2: Custom MCP Server (Long-term)
1. **Discord MCP Server** (`src/discord_mcp_server.py`):
   - MCP tools: `listen_to_discord`, `get_transcription`, `speak_in_discord`
   - Direct WebSocket connection to existing STT client
   - Discord-aware commands and context

2. **Enhanced Voice Commands**:
   - "Claude, explain this error" → screenshot + code analysis
   - "Claude, commit these changes" → git integration
   - "Claude, read the logs" → Docker log analysis

## Technical Requirements

### Dependencies
```txt
# Add to requirements.txt
fastapi>=0.104.0
uvicorn>=0.24.0
sse-starlette>=1.6.5
```

### Environment Configuration
```bash
# Claude Code Integration
VOICEMODE_STT_BASE_URL="http://localhost:9091/v1"
VOICEMODE_TTS_BASE_URL="http://localhost:8080/v1"
CLAUDE_CODE_VOICE_ENABLED=true
DISCORD_STT_BRIDGE_PORT=9091
```

### Docker Compose Updates
```yaml
# Add to existing docker-compose.yml
services:
  app:
    ports:
      - "8000:8000"
      - "9091:9091"  # STT HTTP bridge
    environment:
      - VOICEMODE_STT_BASE_URL=http://localhost:9091/v1
```

## Success Criteria

### Phase 1 Completion
- [ ] HTTP bridge server running on port 9091
- [ ] Voice-mode MCP connects to Discord STT bridge
- [ ] End-to-end: Discord voice → Claude Code response
- [ ] Transcription latency < 2 seconds
- [ ] No regression in existing Discord bot functionality

### Phase 2 Completion
- [ ] Custom Discord MCP server operational
- [ ] Discord-aware voice commands working
- [ ] Multi-user voice command handling
- [ ] TTS responses play in Discord voice channel
- [ ] Git integration via voice commands

### System Integration Tests
- [ ] User speaks in Discord → Claude Code executes command → TTS response
- [ ] Multiple users can issue voice commands without interference
- [ ] Error handling: STT failures, Claude Code timeouts, TTS errors
- [ ] Docker log validation shows clean service communication

## Implementation Files

### New Files
- `src/stt_http_bridge.py` - HTTP API bridge server
- `src/discord_mcp_server.py` - Custom MCP server (Phase 2)
- `config/voice_integration_config.json` - Integration settings

### Modified Files
- `src/stt_client.py` - Add HTTP bridge functionality
- `docker-compose.yml` - Add bridge port and environment variables
- `requirements.txt` - Add FastAPI and MCP dependencies
- `CLAUDE.md` - Update with voice integration commands

## Testing Strategy

### Development Testing
1. **Docker Logs Validation** (per CLAUDE.md requirements):
   ```bash
   docker-compose up --build
   docker-compose logs -f app     # Monitor Discord bot
   docker-compose logs -f whisper-stt  # Monitor STT service
   ```

2. **Integration Testing**:
   ```bash
   # Test STT bridge API
   curl -X POST http://localhost:9091/v1/audio/transcriptions \
     -H "Content-Type: application/json" \
     -d '{"test": true}'
   
   # Test voice-mode connection
   claude mcp status voice-mode
   ```

3. **End-to-End Testing**:
   - Join Discord voice channel
   - Speak command: "Claude, list files in current directory"
   - Verify: STT → HTTP bridge → Claude Code → response
   - Check Docker logs for error-free operation

### Performance Benchmarks
- **Transcription Latency**: < 2 seconds from speech to text
- **Command Execution**: < 5 seconds for simple commands
- **TTS Response**: < 3 seconds for short responses
- **Memory Usage**: < 500MB additional for integration components

## Development Commands

### Setup Voice Integration
```bash
# Install Claude Code
npm install -g @anthropic-ai/claude-code

# Install voice-mode MCP
claude mcp add voice-mode --env OPENAI_API_KEY=dummy

# Configure for Discord STT bridge
export VOICEMODE_STT_BASE_URL="http://localhost:9091/v1"
export VOICEMODE_TTS_BASE_URL="http://localhost:8080/v1"

# Start integrated system
docker-compose up --build
claude converse  # Start voice-enabled Claude Code
```

### Debug Commands
```bash
# Test STT bridge health
curl http://localhost:9091/health

# Monitor transcription stream
curl http://localhost:9091/v1/stream

# Check MCP server status
claude mcp list
claude mcp status voice-mode
```

## Future Enhancements

### Advanced Voice Features
- **Speaker Recognition**: Identify and tag different Discord users
- **Context Awareness**: Remember conversation history per user
- **Multi-language Support**: Dynamic language switching via voice commands
- **Voice Authentication**: Secure command execution via voice biometrics

### Claude Code Integration
- **Visual Context**: Screenshot integration for debugging assistance
- **Git Workflow**: Voice-driven commit, push, and PR creation
- **Real-time Collaboration**: Multiple developers with shared Claude Code session
- **Custom Voice Commands**: Project-specific command shortcuts

---

**Note**: This integration preserves the specialized Discord voice capture system (363-line STT client with VAD, resampling, and multi-user support) while adding Claude Code conversational capabilities through the established MCP protocol.