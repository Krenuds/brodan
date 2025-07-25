from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
import io
import wave
import tempfile
import os
import subprocess

app = FastAPI()

class SynthesizeRequest(BaseModel):
    text: str
    voice: str = "en_GB-alba-medium"
    format: str = "wav"

@app.post("/synthesize")
async def synthesize(request: SynthesizeRequest):
    """Synthesize text to speech using Piper TTS"""
    try:
        # Create temporary file for audio output
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as audio_file:
            audio_file_path = audio_file.name
        
        # Use Piper TTS command line (simpler and handles model downloads)
        try:
            # Use subprocess to call piper with downloaded model
            model_path = f"/models/{request.voice}.onnx"
            result = subprocess.run([
                "bash", "-c", 
                f"echo '{request.text}' | piper --model {model_path} --output-file {audio_file_path}"
            ], 
            capture_output=True, 
            text=True
            )
            
            if result.returncode != 0:
                raise HTTPException(status_code=500, detail=f"Piper failed: {result.stderr}")
            
            # Read the generated audio file
            if not os.path.exists(audio_file_path):
                raise HTTPException(status_code=500, detail="Audio file was not generated")
                
            with open(audio_file_path, 'rb') as f:
                audio_content = f.read()
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"TTS Error: {str(e)}")
            
        # Clean up temp file
        if os.path.exists(audio_file_path):
            os.unlink(audio_file_path)
        
        # No cleanup needed for Python API
        
        # Return audio as WAV
        return Response(
            content=audio_content,
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