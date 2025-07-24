import requests
import io
from typing import Optional
import time

class PiperTTSClient:
    """HTTP client for Piper TTS service"""
    
    def __init__(self, host="piper-tts", port=8080):
        self.base_url = f"http://{host}:{port}"
        self.voice = "en_US-lessac-medium"
        
    async def synthesize(self, text: str) -> Optional[bytes]:
        """Convert text to speech"""
        try:
            response = requests.post(
                f"{self.base_url}/synthesize",
                json={
                    "text": text,
                    "voice": self.voice,
                    "format": "wav"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"TTS Response: {result}")
                # For now, return placeholder data since we're testing connectivity
                return b"placeholder_audio_data"
            else:
                print(f"TTS Error: {response.status_code} - {response.text}")
                return None
                
        except requests.RequestException as e:
            print(f"TTS Request Error: {e}")
            return None
    
    def test_connection(self):
        """Test basic connectivity to TTS service"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                result = response.json()
                print(f"TTS Health Check: {result}")
                return True
            else:
                print(f"TTS Health Check Failed: {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"TTS connection test failed: {e}")
            return False
    
    def get_voices(self):
        """Get available voices (placeholder)"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except requests.RequestException as e:
            print(f"Error getting voices: {e}")
            return None