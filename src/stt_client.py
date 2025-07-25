import websocket
import json
import threading
from queue import Queue
import time
import numpy as np
import uuid
import struct
import logging

# Configure STT client logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class WhisperLiveClient:
    """WebSocket client for WhisperLive STT service"""
    
    def __init__(self, host="whisper-stt", port=9090):
        self.url = f"ws://{host}:{port}"
        self.ws = None
        self.transcription_queue = Queue()
        self.connected = False
        self.ws_thread = None
        self.uid = str(uuid.uuid4())
        self.handshake_complete = False
        self.segment_timeout = 3.0  # 3 seconds timeout for partial segments
        self.timeout_thread = None
        self.timeout_active = False
        
    def connect(self):
        """Establish WebSocket connection"""
        try:
            self.ws = websocket.WebSocketApp(
                self.url,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )
            
            # Run in separate thread
            self.ws_thread = threading.Thread(target=self.ws.run_forever)
            self.ws_thread.daemon = True
            self.ws_thread.start()
            
            # Wait a bit for connection to establish
            time.sleep(2)
            return self.connected
            
        except Exception as e:
            print(f"STT Connection Error: {e}")
            return False
    
    def _on_open(self, ws):
        """Handle WebSocket connection opened"""
        print("STT WebSocket connected")
        self.connected = True
        # Send handshake options
        self._send_handshake()
    
    def _send_handshake(self):
        """Send initial handshake options to WhisperLive server"""
        try:
            # Clear processed segments on new session
            self._processed_segments = {}  # Track by timestamp: {(start, end): {'text', 'completed', 'last_update'}}
            self._start_timeout_monitor()
            
            options = {
                "uid": self.uid,
                "language": "en",
                "task": "transcribe",
                "model": "small",
                "use_vad": True,   # Enable VAD for natural speech boundaries
                # VAD parameters for faster segment finalization
                "min_silence_duration_ms": 1000,    # 1 second silence before completing segment
                "min_speech_duration_ms": 250,      # Minimum speech to avoid noise
                "max_speech_duration_s": 30,        # Split very long segments
                "speech_pad_ms": 200,               # Less padding for faster completion
                "threshold": 0.5                    # Speech detection sensitivity
            }
            self.ws.send(json.dumps(options))
            self.handshake_complete = True
            print("STT handshake sent (VAD enabled with 1s timeout)")
        except Exception as e:
            print(f"STT handshake error: {e}")
    
    def _on_message(self, ws, message):
        """Handle transcription results"""
        try:
            result = json.loads(message)
            print(f"📡 STT Raw Result: {result}")
            
            # Skip server ready messages
            if result.get("message") == "SERVER_READY":
                return
            
            # Handle WhisperLive segments format
            if result.get("segments"):
                # Initialize tracking if needed
                if not hasattr(self, '_processed_segments'):
                    self._processed_segments = {}  # Track by timestamp: {(start, end): {'text', 'completed', 'last_update'}}
                
                # Process segments using timestamp-based tracking
                for segment in result["segments"]:
                    text = segment.get("text", "").strip()
                    if not text:
                        continue
                        
                    # Use start/end timestamps as unique segment identifier
                    start_time = float(segment.get("start", 0))
                    end_time = float(segment.get("end", 0))
                    segment_key = (start_time, end_time)
                    completed = segment.get("completed", True)
                    
                    # Check if this is a new segment or an update to existing segment
                    should_process = False
                    
                    if segment_key not in self._processed_segments:
                        # New segment - always process
                        should_process = True
                        self._processed_segments[segment_key] = {
                            'text': text,
                            'completed': completed,
                            'last_update': time.time()
                        }
                    else:
                        # Existing segment - check if it's been updated
                        prev_segment = self._processed_segments[segment_key]
                        
                        # Process if: text changed OR completion status changed
                        if (text != prev_segment['text'] or 
                            completed != prev_segment['completed']):
                            should_process = True
                            # Update tracking
                            self._processed_segments[segment_key] = {
                                'text': text,
                                'completed': completed,
                                'last_update': time.time()
                            }
                    
                    if should_process:
                        # Create transcription result with segment info
                        transcription = {
                            "text": text,
                            "start": segment.get("start"),
                            "end": segment.get("end"),
                            "completed": completed,
                            "uid": result.get("uid"),
                            "type": "partial" if not completed else "final"
                        }
                        
                        # Log the transcription immediately
                        status = "🔄 PARTIAL" if not completed else "✅ FINAL"
                        print(f"{status} STT: '{text}' ({start_time}s - {end_time}s)")
                        
                        self.transcription_queue.put(transcription)
            
            # Handle direct text format (fallback for other message types)
            elif result.get("text") and result.get("text").strip():
                self.transcription_queue.put(result)
            elif result.get("partial") and result.get("partial").strip():
                # Handle partial transcriptions if available
                partial_result = {"text": result.get("partial"), "type": "partial"}
                print(f"🔄 STT Partial: {result.get('partial')}")
                self.transcription_queue.put(partial_result)
                
        except json.JSONDecodeError as e:
            print(f"STT JSON decode error: {e}")
            print(f"Raw message: {message}")
    
    def _on_error(self, ws, error):
        """Handle WebSocket errors"""
        print(f"STT WebSocket error: {error}")
        self.connected = False
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket connection closed"""
        print("STT WebSocket connection closed")
        self.connected = False
    
    async def send_audio(self, audio_chunk: bytes):
        """Send audio chunk to WhisperLive as float32 numpy array"""
        if self.ws and self.connected and self.handshake_complete:
            try:
                # Convert PCM bytes to float32 numpy array
                audio_array = self._pcm_to_float32(audio_chunk)
                if audio_array is not None:
                    # Send as binary WebSocket message
                    self.ws.send(audio_array.tobytes(), opcode=websocket.ABNF.OPCODE_BINARY)
                    return True
            except Exception as e:
                print(f"Error sending audio: {e}")
                return False
        return False
    
    def _pcm_to_float32(self, pcm_data: bytes) -> np.ndarray:
        """Convert PCM bytes to float32 numpy array and resample to 16kHz"""
        try:
            # Convert 16-bit PCM to numpy array
            if len(pcm_data) < 2:
                return None
            
            # Unpack as 16-bit signed integers  
            samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
            
            # Convert to float32 and normalize to [-1, 1]
            audio_array = np.array(samples, dtype=np.float32) / 32768.0
            
            # Resample from 48kHz (Discord) to 16kHz (WhisperLive requirement)
            # Simple downsampling: take every 3rd sample (48000/16000 = 3)
            resampled_array = audio_array[::3]
            
            return resampled_array
            
        except Exception as e:
            print(f"PCM to float32 conversion error: {e}")
            return None
    
    def get_transcription(self):
        """Get latest transcription if available"""
        if not self.transcription_queue.empty():
            return self.transcription_queue.get()
        return None
    
    def test_connection(self):
        """Test basic connectivity to STT service"""
        try:
            # Simple connection test
            test_ws = websocket.create_connection(self.url, timeout=5)
            test_ws.close()
            return True
        except Exception as e:
            print(f"STT connection test failed: {e}")
            return False
    
    def _start_timeout_monitor(self):
        """Start timeout monitoring thread"""
        if self.timeout_thread and self.timeout_thread.is_alive():
            self.timeout_active = False
            self.timeout_thread.join()
        
        self.timeout_active = True
        self.timeout_thread = threading.Thread(target=self._monitor_segment_timeouts)
        self.timeout_thread.daemon = True
        self.timeout_thread.start()
    
    def _monitor_segment_timeouts(self):
        """Monitor partial segments and auto-complete them after timeout"""
        while self.timeout_active and self.connected:
            try:
                current_time = time.time()
                segments_to_complete = []
                
                # Check for timed-out partial segments
                for segment_key, segment_data in self._processed_segments.items():
                    if (not segment_data.get('completed', True) and 
                        current_time - segment_data.get('last_update', current_time) > self.segment_timeout):
                        segments_to_complete.append(segment_key)
                
                # Auto-complete timed-out segments
                for segment_key in segments_to_complete:
                    if segment_key in self._processed_segments:
                        segment_data = self._processed_segments[segment_key]
                        segment_data['completed'] = True
                        
                        # Create final transcription for timed-out segment
                        transcription = {
                            "text": segment_data['text'],
                            "start": str(segment_key[0]),
                            "end": str(segment_key[1]),
                            "completed": True,
                            "uid": self.uid,
                            "type": "final"
                        }
                        
                        print(f"⏰ TIMEOUT FINAL STT: '{segment_data['text']}' ({segment_key[0]}s - {segment_key[1]}s)")
                        self.transcription_queue.put(transcription)
                
                time.sleep(0.5)  # Check every 500ms
                
            except Exception as e:
                print(f"Error in timeout monitor: {e}")
                time.sleep(1)
    
    def disconnect(self):
        """Clean disconnect"""
        print("Disconnecting STT client...")
        self.connected = False
        self.handshake_complete = False
        self.timeout_active = False
        
        try:
            if self.ws:
                # Send close frame properly
                self.ws.close()
                self.ws = None
        except Exception as e:
            print(f"Error closing WebSocket: {e}")
        
        try:
            if self.ws_thread and self.ws_thread.is_alive():
                self.ws_thread.join(timeout=5)
                if self.ws_thread.is_alive():
                    print("Warning: STT thread did not terminate cleanly")
        except Exception as e:
            print(f"Error joining STT thread: {e}")
        
        print("STT client disconnected")