import websocket
import json
import threading
from queue import Queue
import time

class WhisperLiveClient:
    """WebSocket client for WhisperLive STT service"""
    
    def __init__(self, host="whisper-stt", port=9090):
        self.url = f"ws://{host}:{port}"
        self.ws = None
        self.transcription_queue = Queue()
        self.connected = False
        self.ws_thread = None
        
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
        """Send audio chunk to WhisperLive"""
        if self.ws and self.connected:
            try:
                self.ws.send(audio_chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                return True
            except Exception as e:
                print(f"Error sending audio: {e}")
                return False
        return False
    
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