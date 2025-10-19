import io
import os
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from faster_whisper import WhisperModel
from pvporcupine import create

from agent_manager import AgentManager
from agents import CalculationAgent, SystemControlAgent
from intent import FastClassifier, LLMClassifier
from tts import PiperTTSNative


def play_audio(wav_bytes: bytes):
    """
    Plays WAV audio data from a byte string.
    This function reads the WAV header to ensure correct playback parameters.
    """
    print(f"[Playback] Received {len(wav_bytes)} bytes of WAV data.")

    if len(wav_bytes) <= 44:
        print("[Playback] ERROR: No valid audio data to play.")
        return

    try:
        with wave.open(io.BytesIO(wav_bytes), 'rb') as wav_file:
            sample_rate = wav_file.getframerate()
            num_channels = wav_file.getnchannels()
            samp_width = wav_file.getsampwidth()
            num_frames = wav_file.getnframes()

            print(f"[Playback] WAV info - Rate: {sample_rate} Hz, Channels: {num_channels}, Width: {samp_width} bytes")

            raw_audio = wav_file.readframes(num_frames)

            if samp_width == 2:
                dtype = np.int16
            elif samp_width == 4:
                dtype = np.int32
            else:
                print(f"[Playback] ERROR: Unsupported sample width: {samp_width}")
                return

            audio_data = np.frombuffer(raw_audio, dtype=dtype)

            print(f"[Playback] Starting playback of {num_frames} frames at {sample_rate} Hz...")
            sd.play(audio_data, samplerate=sample_rate, blocking=True)
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
        print("ERROR: ACCESS_KEY not found in .env file.")
        return

    project_root = Path(__file__).parent
    model_path = project_root / "models"
    data_path = project_root / "data"

    porcupine_model_path = str(model_path / "porcupine" / "porcupine_params.pv")
    porcupine_keyword_path = str(model_path / "porcupine" / "Hey-Loki.ppn")
    intents_json_path = data_path / "intents.json"
    piper_model_path = str(model_path / "piper" / "en_US-hfc_male-medium.onnx")

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
                    num_frames_to_record = int(SAMPLE_RATE / FRAME_LENGTH * RECORD_SECONDS)

                    # Pre-allocate buffer - use a list for simpler appending
                    audio_chunks = []
                    for i in range(num_frames_to_record):
                        chunk, _ = stream.read(FRAME_LENGTH)
                        audio_chunks.append(chunk.flatten())  # Flatten to 1D immediately

                    # Concatenate all chunks into a single array
                    audio_int16 = np.concatenate(audio_chunks)
                    audio_float32 = audio_int16.astype(np.float32) / 32768.0

                    print("Transcribing...")
                    segments, _ = whisper.transcribe(audio_float32, language="en")
                    transcription = " ".join(s.text for s in segments).strip()

                    if not transcription:
                        print("--> Heard nothing.")
                        play_audio(tts.speak("I did not hear anything."))
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
