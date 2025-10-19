# test_piper.py

import os
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd
from piper.voice import PiperVoice
import logging
logging.basicConfig(level=logging.DEBUG)

# --- Configuration ---
PROJECT_ROOT = Path(__file__).parent
PIPER_DIR = PROJECT_ROOT / "models" / "piper"
MODEL_PATH = str(PIPER_DIR / "en_US-hfc_male-medium.onnx")
ESPEAK_DATA_PATH = str(PIPER_DIR / "espeak-ng-data")


def main():
    """Main function to test Piper TTS."""
    print("--- Piper TTS Test Script ---")

    # Set the espeak-ng data path environment variable
    print(f"Setting ESPEAK_DATA_PATH to: {ESPEAK_DATA_PATH}")
    os.environ['ESPEAK_DATA_PATH'] = ESPEAK_DATA_PATH

    model_file = Path(MODEL_PATH)
    if not model_file.exists():
        print(f"ERROR: Model file not found at '{MODEL_PATH}'")
        return

    espeak_data_dir = Path(ESPEAK_DATA_PATH)
    if not espeak_data_dir.exists():
        print(f"ERROR: espeak-ng-data directory not found at '{ESPEAK_DATA_PATH}'")
        return

    try:
        print(f"Loading model: {model_file.name}...")
        voice = PiperVoice.load(str(model_file))
        print("Model loaded successfully.")
        print(f"Voice config - Sample rate: {voice.config.sample_rate} Hz")

        text_to_speak = "Hello, this is a test of the Piper text to speech system."
        print(f"Synthesizing text: '{text_to_speak}'")

        # Method 1: Use synthesize_wav - this should return WAV bytes!
        print("\n--- Using synthesize_wav method ---")
        output_file = "test_output.wav"

        try:
            print("Calling voice.synthesize_wav()...")

            # synthesize_wav needs a wave.Wave_write object
            # Open file in binary write mode and wrap with wave.open
            with open(output_file, 'wb') as f:
                with wave.open(f, 'wb') as wav_file:
                    print("Created Wave_write object, calling synthesize_wav()...")
                    voice.synthesize_wav(text_to_speak, wav_file)

            print(f"synthesize_wav() completed")

            # Check if file was created
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"Output file created: {file_size} bytes")

                if file_size > 44:
                    # Read and play
                    print("\nReading and playing audio...")
                    with wave.open(output_file, 'rb') as wav_read:
                        sample_rate = wav_read.getframerate()
                        num_channels = wav_read.getnchannels()
                        num_frames = wav_read.getnframes()
                        duration = num_frames / sample_rate if sample_rate > 0 else 0

                        print(f"WAV file info:")
                        print(f"  Sample rate: {sample_rate} Hz")
                        print(f"  Channels: {num_channels}")
                        print(f"  Frames: {num_frames}")
                        print(f"  Duration: {duration:.2f} seconds")

                        raw_audio = wav_read.readframes(num_frames)
                        audio_data = np.frombuffer(raw_audio, dtype=np.int16)

                        print("\nPlaying audio...")
                        sd.play(audio_data, samplerate=sample_rate, blocking=True)
                        print("\n✓ SUCCESS! Audio playback completed.")
                else:
                    print("✗ File only contains header, no audio data")
            else:
                print("✗ File was not created")

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Clean up
            if os.path.exists(output_file):
                os.remove(output_file)
                print(f"Cleaned up: {output_file}")

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()