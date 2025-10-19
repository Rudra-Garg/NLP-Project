import io
import wave
from pathlib import Path

# This is the correct import from the piper-tts library
from piper.voice import PiperVoice


class PiperTTSNative:
    """Native Python wrapper for Piper TTS - no subprocess needed."""

    def __init__(self, model_path: str):
        print("Initializing Piper TTS (native Python)...")
        self.model_path = Path(model_path)

        if not self.model_path.exists():
            raise FileNotFoundError(f"Piper model not found at: {self.model_path}")

        # Load the voice model
        self.voice = PiperVoice.load(str(self.model_path))
        print("Piper TTS initialized successfully.")

    def speak(self, text: str) -> bytes:
        """Synthesizes text and returns WAV audio as bytes."""
        print(f"[PiperTTS] Synthesizing text: '{text}'...")

        try:
            # Create an in-memory binary buffer
            wav_buffer = io.BytesIO()

            # Wrap it with wave.open to create a Wave_write object
            with wave.open(wav_buffer, 'wb') as wav_file:
                # synthesize_wav will configure and write to the wav_file
                self.voice.synthesize_wav(text, wav_file)

            # Get the complete WAV data
            audio_data = wav_buffer.getvalue()

            print(f"[PiperTTS] Synthesized {len(audio_data)} bytes of WAV data.")
            return audio_data

        except Exception as e:
            print(f"[PiperTTS] ERROR: Failed to synthesize text '{text}': {e}")
            import traceback
            traceback.print_exc()
            return b''

    def close(self):
        """Cleanup resources."""
        print("Piper TTS shutdown.")
        # No specific close/cleanup method is needed for PiperVoice
        pass
