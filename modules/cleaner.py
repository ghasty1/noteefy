import noisereduce as nr
import soundfile as sf
import os
import numpy as np

class AudioCleaner:
    def __init__(self):
        pass

    def clean_audio(self, input_path, aggressive=False):
        """
        Reads audio, performs noise reduction, and saves to a new file.
        Returns the path to the cleaned file.
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        print(f"Loading audio for cleaning: {input_path}...")
        # Load audio (soundfile reads as float32 by default)
        data, rate = sf.read(input_path)

        # Handle stereo by converting to mono if necessary, or just process as is (nr supports multi-channel)
        # Mono is generally sufficient for voice-based recordings.

        print("Performing noise reduction...")
        # prop_decrease: how much to reduce noise (1.0 = 100%)
        # stationary: True assumes constant background noise (fan, hvac)
        prop_decrease = 1.0 if aggressive else 0.75
        
        reduced_noise = nr.reduce_noise(
            y=data, 
            sr=rate, 
            prop_decrease=prop_decrease, 
            stationary=True
        )

        dir_name = os.path.dirname(input_path)
        base_name = os.path.basename(input_path)
        name, ext = os.path.splitext(base_name)
        output_path = os.path.join(dir_name, f"{name}_clean{ext}")

        print(f"Saving cleaned audio to: {output_path}")
        sf.write(output_path, reduced_noise, rate)
        
        return output_path

if __name__ == "__main__":
    # Test script
    import sys
    if len(sys.argv) > 1:
        cleaner = AudioCleaner()
        cleaner.clean_audio(sys.argv[1])
    else:
        print("Usage: python cleaner.py <wav_file>")
