import websocket
import json
import threading
from queue import Queue
import time
import numpy as np
import uuid
import struct

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
            options = {
                "uid": self.uid,
                "language": "en",
                "task": "transcribe",
                "model": "small",
                "use_vad": True
            }
            self.ws.send(json.dumps(options))
            self.handshake_complete = True
            print("STT handshake sent")
        except Exception as e:
            print(f"STT handshake error: {e}")
    
    def _on_message(self, ws, message):
        """Handle transcription results"""
        try:
            result = json.loads(message)
            if result.get("text"):
                print(f"STT Result: {result}")
                self.transcription_queue.put(result)
        except json.JSONDecodeError as e:
            print(f"STT JSON decode error: {e}")
    
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
        """Convert PCM bytes to float32 numpy array"""
        try:
            # Convert 16-bit PCM to numpy array
            if len(pcm_data) < 2:
                return None
            
            # Unpack as 16-bit signed integers
            samples = struct.unpack(f'<{len(pcm_data)//2}h', pcm_data)
            
            # Convert to float32 and normalize to [-1, 1]
            audio_array = np.array(samples, dtype=np.float32) / 32768.0
            
            return audio_array
            
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
    
    def disconnect(self):
        """Clean disconnect"""
        self.connected = False
        if self.ws:
            self.ws.close()
        if self.ws_thread:
            self.ws_thread.join(timeout=5)