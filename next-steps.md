# Next Steps - Discord Voice Bot Development

## Current Status ✅
- Discord bot connected and responding to commands
- All 3 services communicating (Bot ↔ TTS ↔ STT)
- Voice channel joining working with PyNaCl
- Basic command structure in place

## Development Roadmap

### **Phase 1: Voice Recording Pipeline**

#### Step 1: Add Audio Sink for Voice Capture
- Implement the `STTAudioSink` class from the design document
- Capture Discord voice data and convert Opus → PCM
- Stream audio chunks to WhisperLive in real-time

#### Step 2: Real-time Transcription Processing
- Set up continuous audio streaming to STT service
- Handle transcription results and detect command phrases
- Add voice activity detection to know when user stops speaking

### **Phase 2: Command Processing Integration**

#### Step 3: Claude Code Integration
- Add command parsing from transcribed text
- Execute commands through Claude Code API/subprocess
- Handle command results and format responses

#### Step 4: Response Generation
- Convert command results to natural language responses
- Send text responses to Piper TTS service
- Stream generated audio back to Discord voice channel

### **Phase 3: Full Pipeline Testing**

#### Step 5: End-to-End Voice Flow
- User speaks → STT → Command execution → TTS → Audio response
- Test with simple commands like "what files are in this directory"
- Add error handling for failed commands or unclear speech

#### Step 6: Multi-user Support & Polish
- Handle multiple users speaking simultaneously
- Add conversation context/memory
- Improve audio quality and reduce latency

## Immediate Next Step

**Implement Voice Recording Pipeline (Phase 1, Step 1)**

The most logical starting point is adding the audio sink to capture and process voice data from Discord users. This involves:

1. Adding the `STTAudioSink` class to `src/audio_processor.py`
2. Updating the bot to use the custom sink when joining voice channels
3. Testing voice capture and streaming to WhisperLive
4. Verifying transcription results in real-time

This establishes the foundation for the entire voice processing pipeline.