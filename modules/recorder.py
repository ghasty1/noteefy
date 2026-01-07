import sounddevice as sd
import soundfile as sf
import numpy as np
import threading
import queue
import time
import os

class AudioRecorder:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        self.is_recording = False
        self.stop_event = threading.Event()
        self.audio_queue = queue.Queue()
        self.thread = None
        self.filename = None

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def _callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status)
        self.audio_queue.put(indata.copy())

    def _record_thread(self, filename):
        """Thread that handles writing audio to disk."""
        # Clean shutdown check
        if os.path.exists(filename):
            os.remove(filename)

        # Basic settings: 16kHz, Mono (Whisper Native)
        samplerate = 16000
        channels = 1

        with sf.SoundFile(filename, mode='x', samplerate=samplerate, channels=channels) as file:
            with sd.InputStream(samplerate=samplerate, channels=channels, callback=self._callback):
                while self.is_recording or not self.audio_queue.empty():
                    try:
                        data = self.audio_queue.get(timeout=0.1)
                        file.write(data)
                    except queue.Empty:
                        if not self.is_recording:
                            break

    def start_recording(self):
        """Starts the recording process."""
        if self.is_recording:
            return

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        self.filename = os.path.join(self.output_dir, f"recording_{timestamp}.wav")
        self.is_recording = True
        self.audio_queue = queue.Queue() # Clear queue
        
        self.thread = threading.Thread(target=self._record_thread, args=(self.filename,))
        self.thread.start()
        print(f"Recording started: {self.filename}")
        return self.filename

    def stop_recording(self):
        """Stops the recording process."""
        if not self.is_recording:
            return

        self.is_recording = False
        if self.thread:
            self.thread.join()
        print("Recording stopped.")
        return self.filename

if __name__ == "__main__":
    # Test script
    recorder = AudioRecorder()
    try:
        recorder.start_recording()
        print("Recording for 5 seconds...")
        time.sleep(5)
    except KeyboardInterrupt:
        pass
    finally:
        name = recorder.stop_recording()
        print(f"Saved to {name}")
