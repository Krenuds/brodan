# Git Log

Generated on: 2025-07-24 21:24:17

## Complete Git History (19 Commits)

### 1. Commit: b0d1e402

- **Author:** Krenuds
- **Date:** 2025-07-24 21:22:11 -0400
- **Subject:** Clean up logging to show only critical data and transcriptions

**Full Commit Message:**
```
Clean up logging to show only critical data and transcriptions

- Set main logging level to WARNING to suppress debug messages
- Updated Discord logger to ERROR level only
- Removed verbose status reporter
- Simplified transcription display to show only final results
- Removed all debug print statements from STT/TTS clients
- Suppressed audio processing debug messages
- Kept only critical error messages and actual transcriptions

The logs now show:
- Bot connection status
- Final transcriptions with 🎤 emoji
- Critical errors only
```

---

### 2. Commit: 547a4090

- **Author:** Krenuds
- **Date:** 2025-07-24 21:19:15 -0400
- **Subject:** Auto-commit: Task completed at Thu Jul 24 09:19:15 PM EDT 2025

**Full Commit Message:**
```
Auto-commit: Task completed at Thu Jul 24 09:19:15 PM EDT 2025

Changes made:
- debug_audio/processed_stt_20250725_010723.wav
- debug_audio/processed_stt_20250725_011228.wav
- debug_audio/processed_stt_20250725_011357.wav
- debug_audio/processed_stt_20250725_011627.wav
- debug_audio/raw_discord_20250725_010723.wav
- debug_audio/raw_discord_20250725_011228.wav
- debug_audio/raw_discord_20250725_011357.wav
- debug_audio/raw_discord_20250725_011627.wav
- makeLogs.py
- src/bot.py

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

### 3. Commit: 23a1072e

- **Author:** Krenuds
- **Date:** 2025-07-24 21:08:37 -0400
- **Subject:** Implement aggressive segment finalization timeout fixes

**Full Commit Message:**
```
Implement aggressive segment finalization timeout fixes

Server-side VAD improvements:
- Add min_silence_duration_ms: 1000 (1 second vs default 2 seconds)
- Add min_speech_duration_ms: 250 to filter noise
- Add speech_pad_ms: 200 for faster completion
- Add threshold: 0.5 for speech detection sensitivity

Client-side timeout mechanism:
- Track last_update timestamp for each segment
- Monitor partial segments every 500ms in background thread
- Auto-complete segments after 3 seconds of no updates
- Prevent 40+ second delays for segment finalization

Expected result: Segments finalize within 1-3 seconds instead of waiting for new speech

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

### 4. Commit: 7b9b2839

- **Author:** Krenuds
- **Date:** 2025-07-24 20:53:53 -0400
- **Subject:** Auto-commit: Task completed at Thu Jul 24 08:53:52 PM EDT 2025

**Full Commit Message:**
```
Auto-commit: Task completed at Thu Jul 24 08:53:52 PM EDT 2025

Changes made:
- debug_audio/processed_stt_20250725_001955.wav
- debug_audio/processed_stt_20250725_002209.wav
- debug_audio/processed_stt_20250725_004931.wav
- debug_audio/processed_stt_20250725_005052.wav
- debug_audio/raw_discord_20250725_002209.wav
- debug_audio/raw_discord_20250725_004931.wav
- debug_audio/raw_discord_20250725_005052.wav

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

### 5. Commit: 03cffbdf

- **Author:** Krenuds
- **Date:** 2025-07-24 20:51:09 -0400
- **Subject:** Fix STT transcription compounding by implementing VAD and timestamp-based segment tracking

**Full Commit Message:**
```
Fix STT transcription compounding by implementing VAD and timestamp-based segment tracking

- Enable VAD (use_vad: True) for natural speech boundaries
- Replace text-based deduplication with timestamp-based segment tracking
- Track segments by (start_time, end_time) tuple as unique identifier
- Only process segments that are new or have updated text/completion status
- Prevents duplicate processing of evolving partial transcripts
- Eliminates cumulative transcript stacking issue

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

### 6. Commit: ac8c8244

- **Author:** Krenuds
- **Date:** 2025-07-24 20:29:07 -0400
- **Subject:** Fix transcription stacking by preventing duplicate segment processing

**Full Commit Message:**
```
Fix transcription stacking by preventing duplicate segment processing

- WhisperLive sends cumulative segments in each result
- Changed segment_key to use text content only (not timing+text)
- Clear processed_segments on new handshake/session
- Now only processes NEW segments, eliminating duplicate transcriptions
- Tested: Shows single transcription instead of stacking repeats

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

### 7. Commit: 9fc005f1

- **Author:** Krenuds
- **Date:** 2025-07-24 20:22:34 -0400
- **Subject:** Auto-commit: Task completed at Thu Jul 24 08:22:34 PM EDT 2025

**Full Commit Message:**
```
Auto-commit: Task completed at Thu Jul 24 08:22:34 PM EDT 2025

Changes made:
- debug_audio/processed_stt_20250725_001955.wav
- debug_audio/processed_stt_20250725_002209.wav
- debug_audio/raw_discord_20250725_001955.wav
- debug_audio/raw_discord_20250725_002209.wav
- src/stt_client.py

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

### 8. Commit: 0c04626f

- **Author:** Krenuds
- **Date:** 2025-07-24 20:18:04 -0400
- **Subject:** Auto-commit: Task completed at Thu Jul 24 08:18:04 PM EDT 2025

**Full Commit Message:**
```
Auto-commit: Task completed at Thu Jul 24 08:18:04 PM EDT 2025

Changes made:
- debug_audio/processed_stt_20250724_233501.wav
- debug_audio/processed_stt_20250724_233722.wav
- debug_audio/processed_stt_20250724_234234.wav
- debug_audio/processed_stt_20250724_234632.wav
- debug_audio/processed_stt_20250724_235541.wav
- debug_audio/raw_discord_20250724_233501.wav
- debug_audio/raw_discord_20250724_233722.wav
- debug_audio/raw_discord_20250724_234234.wav
- debug_audio/raw_discord_20250724_234632.wav
- debug_audio/raw_discord_20250724_235541.wav

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

### 9. Commit: 55e39504

- **Author:** Krenuds
- **Date:** 2025-07-24 19:56:33 -0400
- **Subject:** Auto-commit: Task completed at Thu Jul 24 07:56:33 PM EDT 2025

**Full Commit Message:**
```
Auto-commit: Task completed at Thu Jul 24 07:56:33 PM EDT 2025

Changes made:
- debug_audio/processed_stt_20250724_234632.wav
- debug_audio/processed_stt_20250724_235541.wav
- debug_audio/raw_discord_20250724_234632.wav
- debug_audio/raw_discord_20250724_235541.wav

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

### 10. Commit: 27b62955

- **Author:** Krenuds
- **Date:** 2025-07-24 19:56:19 -0400
- **Subject:** Fix Discord voice transcription issues

**Full Commit Message:**
```
Fix Discord voice transcription issues

- Add missing format_audio method to STTAudioSink to prevent AttributeError crashes
- Disable aggressive VAD filtering in WhisperLive to improve transcription accuracy
- Improve stereo-to-mono audio conversion by mixing channels instead of taking left only
- Fix WebSocket cleanup issues with proper disconnect handling
- Add duplicate segment prevention in STT message processing
- Tested: Application now properly transcribes speech without crashes or excessive filtering

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

### 11. Commit: 929b3607

- **Author:** Krenuds
- **Date:** 2025-07-24 19:46:56 -0400
- **Subject:** Auto-commit: Task completed at Thu Jul 24 07:46:56 PM EDT 2025

**Full Commit Message:**
```
Auto-commit: Task completed at Thu Jul 24 07:46:56 PM EDT 2025

Changes made:
- debug_audio/processed_stt_20250724_234234.wav
- debug_audio/processed_stt_20250724_234632.wav
- debug_audio/raw_discord_20250724_234234.wav
- debug_audio/raw_discord_20250724_234632.wav
- src/audio_processor.py
- src/stt_client.py

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

### 12. Commit: cde208cb

- **Author:** Krenuds
- **Date:** 2025-07-24 19:39:15 -0400
- **Subject:** Auto-commit: Task completed at Thu Jul 24 07:39:15 PM EDT 2025

**Full Commit Message:**
```
Auto-commit: Task completed at Thu Jul 24 07:39:15 PM EDT 2025

Changes made:
- debug_audio/processed_stt_20250724_233722.wav
- debug_audio/raw_discord_20250724_233722.wav
- src/audio_processor.py

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

### 13. Commit: feb53b7d

- **Author:** Krenuds
- **Date:** 2025-07-24 19:36:05 -0400
- **Subject:** Auto-commit: Task completed at Thu Jul 24 07:36:05 PM EDT 2025

**Full Commit Message:**
```
Auto-commit: Task completed at Thu Jul 24 07:36:05 PM EDT 2025

Changes made:
- Dockerfile
- debug_audio/processed_stt_20250724_233501.wav
- debug_audio/raw_discord_20250724_233501.wav
- src/audio_debug.py
- src/audio_processor.py
- src/bot.py

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

### 14. Commit: 92e04489

- **Author:** Krenuds
- **Date:** 2025-07-24 19:28:22 -0400
- **Subject:** Enhance STT live transcription parsing and monitoring system

**Full Commit Message:**
```
Enhance STT live transcription parsing and monitoring system

- Fix STT parsing to correctly handle WhisperLive segments format with start/end times
- Add enhanced transcription display with visual formatting for partial vs final results
- Implement periodic system status reporting every 30 seconds showing STT/voice/recording status
- Add audio processing metrics logging every 100 chunks to monitor data flow
- Improve error handling and connection monitoring throughout STT pipeline

The live transcription logs now show properly formatted output with timing information
and clear visual distinction between partial and final transcription results. System
health monitoring provides regular status updates for troubleshooting.

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

### 15. Commit: e4be8b13

- **Author:** Krenuds
- **Date:** 2025-07-24 19:21:27 -0400
- **Subject:** Add comprehensive Python debugging configuration to diagnose STT issues

**Full Commit Message:**
```
Add comprehensive Python debugging configuration to diagnose STT issues

CONTEXT: Got derailed debugging STT transcription problems - added multiple fixes
(VAD threshold adjustments, connection management, callback fixes) but weren't
seeing the actual original logs due to docker-compose log buffering/visibility.

BACKTRACKING STRATEGY: Reset to commit e7458d7 to see original STT issue, which
revealed the root cause: AttributeError: 'STTAudioSink' object has no attribute 'format_audio'

DEBUGGING ENHANCEMENTS:
- Added PYTHONDEBUG=1, PYTHONWARNINGS=all, PYTHONASYNCIODEBUG=1 to docker-compose.yml
- Configured comprehensive logging in bot.py with DEBUG level and structured format
- Added discord.py debug logging to see WebSocket frames and voice connection details
- Added STT client debug logger for detailed connection troubleshooting

CURRENT STATE: Now at commit e7458d7 with enhanced debugging to properly diagnose
the original format_audio method missing from STTAudioSink class.

Next: Fix the actual AttributeError that was causing STT service crashes.

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

### 16. Commit: e7458d76

- **Author:** Krenuds
- **Date:** 2025-07-24 17:34:02 -0400
- **Subject:** Enhance STT transcription parsing and console display

**Full Commit Message:**
```
Enhance STT transcription parsing and console display

- Add formatted transcription display with proper visual separation
- Show metadata like language, confidence, and timestamp when available
- Improve STT message parsing to handle partial transcriptions
- Add detailed raw result logging for debugging
- Better error handling with raw message display on JSON decode errors

The system now properly parses and displays:
- Complete transcriptions with formatting
- Partial transcriptions during speech
- Server status messages (SERVER_READY)
- Enhanced console output for better visibility

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

### 17. Commit: 0991485d

- **Author:** Krenuds
- **Date:** 2025-07-24 17:28:56 -0400
- **Subject:** Fix STT WebSocket connection issues

**Full Commit Message:**
```
Fix STT WebSocket connection issues

- Implement proper WhisperLive handshake with JSON options (uid, language, task)
- Convert Discord PCM audio to float32 numpy arrays for WhisperLive compatibility
- Add numpy dependency to requirements.txt
- Fix UTF-8 decode errors by sending binary audio data after handshake
- Establish stable WebSocket connection with STT service

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

### 18. Commit: ec9be5cc

- **Author:** Krenuds
- **Date:** 2025-07-24 17:23:19 -0400
- **Subject:** Implement Phase 1: Voice Recording Pipeline (Steps 1-2)

**Full Commit Message:**
```
Implement Phase 1: Voice Recording Pipeline (Steps 1-2)

Added complete voice capture and STT streaming functionality:

**New Components:**
- src/audio_processor.py: Custom STTAudioSink class for Discord voice capture
  - Voice activity detection using energy-based thresholding
  - Stereo to mono audio conversion for STT compatibility
  - Thread-safe WebSocket streaming to WhisperLive service
  - AudioProcessor coordinator class for managing voice pipeline

**Bot Integration:**
- Updated src/bot.py with audio processor integration
- Auto-start voice recording when joining Discord channels
- Real-time transcription monitoring with 100ms polling
- Voice state management for recording control

**Infrastructure:**
- Removed completed next-steps.md file
- Updated CLAUDE.md with simplified command documentation

**Testing Results:**
- Successfully connects to Discord voice channels
- STT WebSocket service connection established
- Voice recording pipeline activates properly
- All 3 services (Bot, STT, TTS) running without errors

Foundation complete for voice capture → STT transcription flow.
Next phase: Command processing and TTS response integration.

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

### 19. Commit: 3f25f30b

- **Author:** Krenuds
- **Date:** 2025-07-24 17:02:53 -0400
- **Subject:** Initial commit: Discord voice bot with STT/TTS integration

**Full Commit Message:**
```
Initial commit: Discord voice bot with STT/TTS integration

- Added Discord bot with py-cord[voice] and PyNaCl support
- Integrated WhisperLive STT service via WebSocket
- Integrated Piper TTS service via HTTP
- Docker Compose setup with 3 services (app, STT, TTS)
- Voice commands: \!ping, \!test, \!join, \!leave
- Service communication testing capabilities
- Added .gitignore to exclude sensitive files

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

