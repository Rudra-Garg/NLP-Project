import io
import wave
from pathlib import Path

import numpy as np

from piper import PiperVoice


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
            # Collect audio chunks and convert to WAV in memory
            audio_chunks = list(self.voice.synthesize(text))

            if not audio_chunks:
                print("[PiperTTS] No audio generated.")
                return b''

            # Extract raw PCM from AudioChunks and get sample rate
            sample_rate = audio_chunks[0].sample_rate if hasattr(audio_chunks[0], 'sample_rate') else 22050

            # Combine all audio data
            audio_arrays = []
            for chunk in audio_chunks:
                # AudioChunk should have numpy array or convertible data
                if hasattr(chunk, 'audio'):
                    audio_arrays.append(np.array(chunk.audio, dtype=np.int16))
                else:
                    audio_arrays.append(np.array(chunk, dtype=np.int16))

            combined_audio = np.concatenate(audio_arrays)

            # Create WAV in memory
            wav_io = io.BytesIO()
            with wave.open(wav_io, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(combined_audio.tobytes())

            audio_data = wav_io.getvalue()
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
        pass
