import os
from pathlib import Path
import io
import wave
import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from faster_whisper import WhisperModel
from pvporcupine import create

from agent_manager import AgentManager
from agents import CalculationAgent, SystemControlAgent
from intent import FastClassifier, LLMClassifier
from tts import PiperTTSNative

try:
    DEFAULT_SAMPLE_RATE = int(sd.query_devices(kind='output')['default_samplerate'])
    print(f"[Audio] Detected default device sample rate: {DEFAULT_SAMPLE_RATE} Hz")
except Exception as e:
    print(f"[Audio] WARNING: Could not detect default sample rate, falling back to 22050 Hz. Error: {e}")
    DEFAULT_SAMPLE_RATE = 22050


def play_audio(tts_output: bytes):
    """Helper function to play audio by properly parsing the WAV file."""
    print(f"[Playback] Received {len(tts_output)} bytes of WAV data.")

    if len(tts_output) <= 44:
        print("[Playback] ERROR: No audio data to play.")
        return

    try:
        # Use wave module to properly parse the WAV file
        with wave.open(io.BytesIO(tts_output), 'rb') as wav_file:
            # Get audio parameters
            n_channels = wav_file.getnchannels()
            sampwidth = wav_file.getsampwidth()  # bytes per sample
            framerate = wav_file.getframerate()
            n_frames = wav_file.getnframes()

            print(f"[Playback] WAV info - Channels: {n_channels}, Sample width: {sampwidth} bytes, Rate: {framerate} Hz, Frames: {n_frames}")

            # Read the raw audio data
            raw_audio = wav_file.readframes(n_frames)

            # Convert based on sample width
            if sampwidth == 2:  # 16-bit
                audio_data = np.frombuffer(raw_audio, dtype=np.int16)
                audio_data = audio_data.astype(np.float32) / 32768.0
            elif sampwidth == 4:  # 32-bit
                audio_data = np.frombuffer(raw_audio, dtype=np.int32)
                audio_data = audio_data.astype(np.float32) / 2147483648.0
            else:
                print(f"[Playback] ERROR: Unsupported sample width: {sampwidth}")
                return

            # If stereo, keep as is; sounddevice handles it
            if n_channels == 2:
                audio_data = audio_data.reshape(-1, 2)

            print(f"[Playback] Starting playback of {len(audio_data)} samples at {framerate} Hz...")
            sd.play(audio_data, samplerate=framerate)
            sd.wait()
            print("[Playback] Playback finished.")

    except Exception as e:
        print(f"[Playback] ERROR: An error occurred during audio playback: {e}")
        import traceback
        traceback.print_exc()


def main():
    # --- 1. Configuration and Initialization ---
    load_dotenv()
    try:
        access_key = os.environ["ACCESS_KEY"]
    except KeyError:
        return

    project_root = Path(__file__).parent
    model_path = project_root / "models"
    data_path = project_root / "data"
    piper_path = project_root / "piper"

    porcupine_model_path = str(model_path / "porcupine" / "porcupine_params.pv")
    porcupine_keyword_path = str(model_path / "porcupine" / "Hey-Loki.ppn")
    intents_json_path = data_path / "intents.json"
    piper_exe_path = str(piper_path / "piper.exe")
    piper_model_path = str(piper_path / "en_US-hfc_male-medium.onnx")

    RECORD_SECONDS = 5
    print("--- Initializing LOKI Components ---")

    porcupine = create(access_key=access_key, model_path=porcupine_model_path, keyword_paths=[porcupine_keyword_path])
    SAMPLE_RATE, FRAME_LENGTH = porcupine.sample_rate, porcupine.frame_length

    print("Loading Whisper model...")
    whisper = WhisperModel("base", device="cpu", compute_type="int8")

    fast_classifier = FastClassifier(intents_json_path)
    llm_classifier = LLMClassifier()

    agent_manager = AgentManager()
    agent_manager.register_agent(CalculationAgent())
    agent_manager.register_agent(SystemControlAgent())

    tts = PiperTTSNative(model_path=piper_model_path)

    print("\n--- LOKI Initialized Successfully ---")
    play_audio(tts.speak("Loki is online."))
    print(f"Listening for 'Hey Loki'...")

    # --- 2. Main Audio Loop ---
    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', blocksize=FRAME_LENGTH) as stream:
            while True:
                pcm, _ = stream.read(FRAME_LENGTH)
                if porcupine.process(pcm.flatten()) >= 0:
                    print("\nWake word detected!")
                    play_audio(tts.speak("Yes?"))

                    print(f"Recording for {RECORD_SECONDS} seconds...")
                    num_frames = int(SAMPLE_RATE / FRAME_LENGTH * RECORD_SECONDS)
                    audio_buffer = [stream.read(FRAME_LENGTH)[0] for _ in range(num_frames)]
                    audio_float32 = np.concatenate(audio_buffer).flatten().astype(np.float32) / 32768.0

                    print("Transcribing...")
                    segments, _ = whisper.transcribe(audio_float32, language="en")
                    transcription = " ".join(s.text for s in segments).strip()

                    if not transcription:
                        print("--> Heard nothing.")
                        play_audio(tts.speak("I didn't hear anything."))
                        print(f"\nListening for 'Hey Loki'...")
                        continue

                    print(f'--> Heard: "{transcription}"')

                    intent = fast_classifier.classify(transcription)
                    print(f'--> Fast Path Intent: {intent}')

                    if intent['type'] == 'unknown' or intent['confidence'] < 0.75:
                        print("Fast path failed. Falling back to LLM Classifier...")
                        intent = llm_classifier.classify(transcription)
                        print(f'--> LLM Path Intent: {intent}')

                    response_text = agent_manager.dispatch(intent)
                    print(f'--> LOKI says: "{response_text}"')

                    play_audio(tts.speak(response_text))
                    print(f"\nListening for 'Hey Loki'...")

    except KeyboardInterrupt:
        print("\nStopping LOKI.")
    finally:
        porcupine.delete()
        tts.close()
        print("Cleaned up resources.")


if __name__ == '__main__':
    main()
