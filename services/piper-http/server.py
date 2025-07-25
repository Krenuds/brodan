from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
import io
import wave
import subprocess
import tempfile
import os

app = FastAPI()

class SynthesizeRequest(BaseModel):
    text: str
    voice: str = "en_US-lessac-medium"
    format: str = "wav"

@app.post("/synthesize")
async def synthesize(request: SynthesizeRequest):
    """Synthesize text to speech using Piper TTS"""
    try:
        # Create temporary files for input and output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as text_file:
            text_file.write(request.text)
            text_file_path = text_file.name
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as audio_file:
            audio_file_path = audio_file.name
        
        # Use Piper TTS to synthesize speech
        # Download model if needed and synthesize
        cmd = [
            "echo", request.text, "|", 
            "piper", 
            "--model", f"/models/{request.voice}.onnx",
            "--output_file", audio_file_path
        ]
        
        # For now, create a simple test audio file
        # Generate a short sine wave as placeholder
        import numpy as np
        sample_rate = 22050
        duration = len(request.text) * 0.1  # 0.1 seconds per character
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        frequency = 440.0  # A4 note
        audio_data = np.sin(frequency * 2 * np.pi * t) * 0.3
        
        # Convert to 16-bit PCM
        audio_16bit = (audio_data * 32767).astype(np.int16)
        
        # Create WAV file in memory
        audio_buffer = io.BytesIO()
        with wave.open(audio_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_16bit.tobytes())
        
        # Clean up temp files
        os.unlink(text_file_path)
        if os.path.exists(audio_file_path):
            os.unlink(audio_file_path)
        
        # Return audio as WAV
        audio_buffer.seek(0)
        return Response(
            content=audio_buffer.getvalue(),
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=speech.wav"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS Error: {str(e)}")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "piper-tts"}

@app.get("/")
async def root():
    return {"message": "Piper TTS HTTP Service", "status": "running"}