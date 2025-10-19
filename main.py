# main.py

import os
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
from tts_manager import TTSManager


def main():
    # --- 1. Load All Configuration from .env File ---
    print("--- Loading Configuration from .env ---")
    load_dotenv()

    # PicoVoice Porcupine
    ACCESS_KEY = os.environ.get("ACCESS_KEY")
    PORCUPINE_MODEL_PATH = os.environ.get("PORCUPINE_MODEL_PATH")
    PORCUPINE_KEYWORD_PATH = os.environ.get("PORCUPINE_KEYWORD_PATH")
    PORCUPINE_SENSITIVITY = float(os.environ.get("PORCUPINE_SENSITIVITY", 0.5))

    # Whisper STT
    WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "small.en")
    WHISPER_DEVICE = os.environ.get("WHISPER_DEVICE", "cpu")
    WHISPER_COMPUTE_TYPE = os.environ.get("WHISPER_COMPUTE_TYPE", "int8")

    # VAD
    VAD_THRESHOLD = float(os.environ.get("VAD_THRESHOLD", 0.01))
    VAD_SILENCE_FRAMES_AFTER_SPEECH = int(os.environ.get("VAD_SILENCE_FRAMES_AFTER_SPEECH", 40))
    VAD_NO_SPEECH_TIMEOUT_FRAMES = int(os.environ.get("VAD_NO_SPEECH_TIMEOUT_FRAMES", 100))
    VAD_MAX_RECORDING_FRAMES = int(os.environ.get("VAD_MAX_RECORDING_FRAMES", 350))

    # Intent Classification
    INTENTS_JSON_PATH = os.environ.get("INTENTS_JSON_PATH")
    FAST_CLASSIFIER_MODEL = os.environ.get("FAST_CLASSIFIER_MODEL")
    FAST_CLASSIFIER_THRESHOLD = float(os.environ.get("FAST_CLASSIFIER_THRESHOLD", 0.80))
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "dolphin-phi")

    # Piper TTS
    PIPER_MODEL_PATH = os.environ.get("PIPER_MODEL_PATH")

    if not ACCESS_KEY:
        print("ERROR: ACCESS_KEY not found in .env file. Please get a key from PicoVoice Console.")
        return

    # --- 2. Initialization ---
    print("\n--- Initializing LOKI Components ---")
    project_root = Path(__file__).parent

    # Resolve relative paths from .env to absolute paths
    porcupine_model_path = str(project_root / PORCUPINE_MODEL_PATH)
    porcupine_keyword_path = str(project_root / PORCUPINE_KEYWORD_PATH)
    intents_json_path = project_root / INTENTS_JSON_PATH
    piper_model_path = str(project_root / PIPER_MODEL_PATH)

    porcupine = create(
        access_key=ACCESS_KEY,
        model_path=porcupine_model_path,
        keyword_paths=[porcupine_keyword_path],
        sensitivities=[PORCUPINE_SENSITIVITY]
    )
    SAMPLE_RATE, FRAME_LENGTH = porcupine.sample_rate, porcupine.frame_length

    print(f"Loading Whisper model '{WHISPER_MODEL_SIZE}' for device '{WHISPER_DEVICE}'...")
    whisper = WhisperModel(WHISPER_MODEL_SIZE, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE_TYPE)

    # Pass configuration to classifiers
    fast_classifier = FastClassifier(
        intents_path=intents_json_path,
        model_name=FAST_CLASSIFIER_MODEL,
        threshold=FAST_CLASSIFIER_THRESHOLD
    )
    llm_classifier = LLMClassifier(model_name=OLLAMA_MODEL)

    agent_manager = AgentManager()
    agent_manager.register_agent(CalculationAgent())
    agent_manager.register_agent(SystemControlAgent())

    tts = PiperTTSNative(model_path=piper_model_path)
    tts_manager = TTSManager(tts_engine=tts)

    print("\n--- LOKI Initialized Successfully ---")
    tts_manager.speak_async("Loki is online.")
    print(f"Listening for 'Hey Loki'...")

    # --- 3. Main Audio Loop ---
    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', blocksize=FRAME_LENGTH) as stream:
            while True:
                pcm, _ = stream.read(FRAME_LENGTH)
                if porcupine.process(pcm.flatten()) >= 0:
                    print("\nWake word detected!")
                    tts_manager.speak_async("Yes?")

                    print("Listening for command...")
                    audio_chunks = []
                    has_started_speaking = False
                    consecutive_silent_frames = 0

                    while True:
                        chunk, _ = stream.read(FRAME_LENGTH)
                        audio_chunks.append(chunk)

                        audio_float32_chunk = chunk.flatten().astype(np.float32) / 32768.0
                        rms = np.sqrt(np.mean(audio_float32_chunk ** 2))

                        if rms > VAD_THRESHOLD:
                            if not has_started_speaking:
                                print("Speech detected...")
                                has_started_speaking = True
                            consecutive_silent_frames = 0
                        else:
                            if has_started_speaking:
                                consecutive_silent_frames += 1

                        if has_started_speaking and consecutive_silent_frames > VAD_SILENCE_FRAMES_AFTER_SPEECH:
                            print("End of speech detected.")
                            break
                        if not has_started_speaking and len(audio_chunks) > VAD_NO_SPEECH_TIMEOUT_FRAMES:
                            print("No speech detected, timing out.")
                            break
                        if len(audio_chunks) > VAD_MAX_RECORDING_FRAMES:
                            print("Maximum recording time reached.")
                            break

                    audio_int16 = np.concatenate([c.flatten() for c in audio_chunks])
                    audio_float32 = audio_int16.astype(np.float32) / 32768.0

                    print("Transcribing...")
                    segments, _ = whisper.transcribe(audio_float32, language="en", vad_filter=True)
                    transcription = " ".join(s.text for s in segments).strip()

                    if not transcription:
                        print("--> Heard nothing.")
                        tts_manager.speak_async("I did not hear anything.")
                        print(f"\nListening for 'Hey Loki'...")
                        continue

                    print(f'--> Heard: "{transcription}"')
                    intent = fast_classifier.classify(transcription)
                    print(f'--> Fast Path Intent: {intent}')

                    if intent['type'] == 'unknown' or intent['confidence'] < FAST_CLASSIFIER_THRESHOLD:
                        print("Fast path failed. Falling back to LLM Classifier...")
                        intent = llm_classifier.classify(transcription)
                        print(f'--> LLM Path Intent: {intent}')

                    response_text = agent_manager.dispatch(intent)
                    print(f'--> LOKI says: "{response_text}"')
                    tts_manager.speak_async(response_text)
                    print(f"\nListening for 'Hey Loki'...")

    except KeyboardInterrupt:
        print("\nStopping LOKI.")
    finally:
        if 'tts_manager' in locals():
            tts_manager.shutdown()
        porcupine.delete()
        tts.close()
        print("Cleaned up resources.")


if __name__ == '__main__':
    main()
