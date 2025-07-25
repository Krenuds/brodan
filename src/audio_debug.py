import wave
import os
import time
from datetime import datetime
import struct
import threading

class AudioDebugger:
    """Debug audio quality by recording raw and processed audio streams"""
    
    def __init__(self, debug_dir="/app/debug_audio"):
        self.debug_dir = debug_dir
        self.recording = False
        self.raw_audio_file = None
        self.processed_audio_file = None
        self.lock = threading.Lock()
        
        # Create debug directory
        os.makedirs(debug_dir, exist_ok=True)
        
    def start_recording(self):
        """Start recording debug audio files"""
        with self.lock:
            if self.recording:
                return
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create WAV files for raw and processed audio
            raw_path = os.path.join(self.debug_dir, f"raw_discord_{timestamp}.wav")
            processed_path = os.path.join(self.debug_dir, f"processed_stt_{timestamp}.wav")
            
            # Discord audio: 48kHz, stereo, 16-bit
            self.raw_audio_file = wave.open(raw_path, 'wb')
            self.raw_audio_file.setnchannels(2)  # Stereo
            self.raw_audio_file.setsampwidth(2)  # 16-bit
            self.raw_audio_file.setframerate(48000)  # 48kHz
            
            # STT processed audio: 48kHz, mono, 16-bit (before float conversion)
            self.processed_audio_file = wave.open(processed_path, 'wb')
            self.processed_audio_file.setnchannels(1)  # Mono
            self.processed_audio_file.setsampwidth(2)  # 16-bit
            self.processed_audio_file.setframerate(48000)  # 48kHz
            
            self.recording = True
    
    def record_raw_audio(self, audio_data: bytes):
        """Record raw audio from Discord"""
        with self.lock:
            if self.recording and self.raw_audio_file:
                try:
                    self.raw_audio_file.writeframes(audio_data)
                except Exception as e:
                    pass  # Silently handle
    
    def record_processed_audio(self, audio_data: bytes):
        """Record processed audio being sent to STT"""
        with self.lock:
            if self.recording and self.processed_audio_file:
                try:
                    self.processed_audio_file.writeframes(audio_data)
                except Exception as e:
                    pass  # Silently handle
    
    def stop_recording(self):
        """Stop recording and close files"""
        with self.lock:
            if not self.recording:
                return
                
            try:
                if self.raw_audio_file:
                    self.raw_audio_file.close()
                    self.raw_audio_file = None
                    
                if self.processed_audio_file:
                    self.processed_audio_file.close()
                    self.processed_audio_file = None
                    
                self.recording = False
                
            except Exception as e:
                pass  # Silently handle
    
    def analyze_audio_files(self):
        """Analyze recorded audio files for debugging"""
        try:
            files = [f for f in os.listdir(self.debug_dir) if f.endswith('.wav')]
            if not files:
                print("No audio debug files found")
                return
                
            print(f"\n🎧 AUDIO DEBUG ANALYSIS:")
            print(f"Found {len(files)} audio files in {self.debug_dir}")
            
            for filename in sorted(files):
                filepath = os.path.join(self.debug_dir, filename)
                try:
                    with wave.open(filepath, 'rb') as wav:
                        duration = wav.getnframes() / wav.getframerate()
                        channels = wav.getnchannels()
                        sample_rate = wav.getframerate()
                        sample_width = wav.getsampwidth()
                        
                        print(f"   📁 {filename}:")
                        print(f"      Duration: {duration:.2f}s")
                        print(f"      Format: {channels}ch, {sample_rate}Hz, {sample_width*8}bit")
                        
                        # Read a sample to check for silence/noise
                        frames = wav.readframes(min(wav.getnframes(), sample_rate))  # First second
                        if frames:
                            samples = struct.unpack(f'<{len(frames)//sample_width}h', frames)
                            max_amplitude = max(abs(s) for s in samples) if samples else 0
                            rms = (sum(s*s for s in samples) / len(samples)) ** 0.5 if samples else 0
                            
                            print(f"      Max amplitude: {max_amplitude} ({max_amplitude/32768*100:.1f}%)")
                            print(f"      RMS level: {rms:.0f}")
                            
                            # Detect potential issues
                            if max_amplitude < 100:
                                print(f"      ⚠️  Very quiet audio - possible silence")
                            elif max_amplitude > 30000:
                                print(f"      ⚠️  Very loud audio - possible clipping")
                            
                except Exception as e:
                    print(f"   Error analyzing {filename}: {e}")
                    
        except Exception as e:
            print(f"Error in audio analysis: {e}")

# Global instance for easy access
audio_debugger = AudioDebugger()