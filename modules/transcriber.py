import requests
import os
import time
import math
import wave
from concurrent.futures import ThreadPoolExecutor

# Optional dependencies
try:
    import lameenc
    HAS_LAME = True
except ImportError:
    HAS_LAME = False

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

try:
    from gradio_client import Client, handle_file
    HAS_GRADIO = True
except ImportError:
    HAS_GRADIO = False

from .crypto_utils import get_bundled_key

class CloudTranscriber:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            self.api_key = get_bundled_key()
        self.client = Groq(api_key=self.api_key) if (self.api_key and HAS_GROQ) else None
        self.parakeet_space = "nvidia/parakeet-tdt-0.6b-v3"

    def transcribe(self, audio_path):
        """
        Orchestrates the transcription process with robust fallbacks.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # 1. Attempt Bundled Compression (High Priority)
        processed_path = audio_path
        was_compressed = False
        
        if HAS_LAME:
            try:
                processed_path = self._compress_to_mp3_lame(audio_path)
                was_compressed = True
            except Exception as e:
                print(f"Note: Bundled compression failed. Sending raw file. {e}")
                processed_path = audio_path
        else:
            print("Note: lameenc not installed. Sending raw WAV file.")

        try:
            # 2. Try NVIDIA Parakeet (Highest Priority - Free & Accurate)
            if HAS_GRADIO:
                try:
                    print(f"Using NVIDIA Parakeet API (Space: {self.parakeet_space})")
                    return self._transcribe_with_parakeet(processed_path)
                except Exception as e:
                    print(f"Parakeet API failed, falling back to Groq... {e}")
            
            # 3. Try Groq (Turbo Cloud - Fallback)
            if self.api_key and self.client:
                try:
                    print(f"Using Groq API Turbo (File: {os.path.basename(processed_path)})")
                    return self._transcribe_with_groq(processed_path)
                except Exception as e:
                    print(f"Groq failed. {e}")
            
            raise ValueError("All transcription backends failed or were not configured. Please check your internet or API keys.")

        finally:
            if was_compressed and processed_path != audio_path:
                try: os.remove(processed_path)
                except: pass

    def _compress_to_mp3_lame(self, wav_path):
        """Zero-dependency WAV to MP3 using lameenc."""
        mp3_path = wav_path.rsplit('.', 1)[0] + ".mp3"
        print(f"Bundled Compression: {os.path.basename(wav_path)} -> MP3...")
        
        with wave.open(wav_path, 'rb') as wav_file:
            n_channels = wav_file.getnchannels()
            sample_rate = wav_file.getframerate()
            n_frames = wav_file.getnframes()
            pcm_data = wav_file.readframes(n_frames)
            
            encoder = lameenc.Encoder()
            encoder.set_bit_rate(32) # 32kbps
            encoder.set_in_sample_rate(sample_rate)
            encoder.set_channels(n_channels)
            encoder.set_quality(5) # Mid quality (fast)
            
            mp3_data = encoder.encode(pcm_data)
            mp3_data += encoder.flush()
            
            with open(mp3_path, 'wb') as mp3_file:
                mp3_file.write(mp3_data)
        
        return mp3_path

    def _transcribe_with_parakeet(self, audio_path):
        """Transcribe using NVIDIA's official Parakeet Space via Gradio."""
        print(f"Connecting to Parakeet V3: {self.parakeet_space}...")
        client = Client(self.parakeet_space)
        result = client.predict(
            audio_path=handle_file(audio_path),
            api_name="/transcribe_file"
        )
        
        # Result is a tuple: [0] Segments Dataframe [1] CSV Path [2] SRT Path
        if not result or len(result) == 0:
            return "Error: Empty response from Parakeet."
            
        segments_info = result[0]
        if isinstance(segments_info, dict) and "data" in segments_info and "headers" in segments_info:
            headers = [h.lower() for h in segments_info["headers"]]
            data = segments_info["data"]
            
            # Find the 'segment' or 'text' column index
            segment_idx = -1
            for i, h in enumerate(headers):
                if "segment" in h or "text" in h:
                    segment_idx = i
                    break
            
            if segment_idx == -1:
                # Fallback to last column if segment/text not found
                segment_idx = len(headers) - 1
            
            text_fragments = []
            for row in data:
                if len(row) > segment_idx:
                    text_fragments.append(str(row[segment_idx]))
            
            full_text = " ".join(text_fragments).strip()
            if not full_text:
                print("Note: Parakeet returned empty text for this segment.")
            return full_text
        
        return "Warning: Could not parse Parakeet response format."

    def _transcribe_with_groq(self, path):
        """Groq transcription with simple file size check."""
        file_size_mb = os.path.getsize(path) / (1024 * 1024)
        if file_size_mb > 24:
            raise RuntimeError(f"File too large for Groq ({file_size_mb:.1f}MB).")

        with open(path, "rb") as file:
            transcription = self.client.audio.transcriptions.create(
                file=(os.path.basename(path), file.read()),
                model="whisper-large-v3",
                response_format="json",
            )
        return transcription.text

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    path = input("Enter audio path: ")
    t = CloudTranscriber()
    try:
        print("Final Transcript:\n", t.transcribe(path))
    except Exception as e:
        print(f"Transcription Error: {e}")
