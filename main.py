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

    print("--- Initializing LOKI Components ---")

    porcupine = create(access_key=access_key, model_path=porcupine_model_path, keyword_paths=[porcupine_keyword_path])
    SAMPLE_RATE, FRAME_LENGTH = porcupine.sample_rate, porcupine.frame_length

    # --- VAD & DYNAMIC RECORDING SETTINGS ---
    VAD_THRESHOLD = 0.01  # Volume threshold for considering audio as speech. Tune this for your mic.
    # Frames of silence to wait for after speech has been detected.
    # 1 second of silence = (SAMPLE_RATE / FRAME_LENGTH) frames. e.g. (16000/512) = ~31 frames/sec.
    # So, 40 frames is ~1.3 seconds of silence.
    SILENT_FRAMES_AFTER_SPEECH = 40
    # Frames of silence to wait for if no speech is detected at all.
    SILENT_FRAMES_NO_SPEECH_TIMEOUT = 100  # About 3 seconds
    # Safety net to prevent infinite recording.
    MAX_RECORDING_FRAMES = 350  # About 10-11 seconds

    print("Loading Whisper model...")
    # Using "small.en" for better accuracy. Change if needed.
    whisper = WhisperModel("small.en", device="cpu", compute_type="int8")

    fast_classifier = FastClassifier(intents_json_path)
    llm_classifier = LLMClassifier()

    agent_manager = AgentManager()
    agent_manager.register_agent(CalculationAgent())
    agent_manager.register_agent(SystemControlAgent())

    tts = PiperTTSNative(model_path=piper_model_path)
    tts_manager = TTSManager(tts_engine=tts)

    print("\n--- LOKI Initialized Successfully ---")
    tts_manager.speak_async("Loki is online.")
    print(f"Listening for 'Hey Loki'...")

    # --- 2. Main Audio Loop ---
    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', blocksize=FRAME_LENGTH) as stream:
            while True:
                pcm, _ = stream.read(FRAME_LENGTH)
                if porcupine.process(pcm.flatten()) >= 0:
                    print("\nWake word detected!")
                    tts_manager.speak_async("Yes?")

                    # --- DYNAMIC RECORDING LOOP ---
                    print("Listening for command...")
                    audio_chunks = []
                    has_started_speaking = False
                    consecutive_silent_frames = 0

                    while True:
                        chunk, _ = stream.read(FRAME_LENGTH)
                        audio_chunks.append(chunk)  # Append the raw int16 chunk

                        # Normalize chunk to float32 for RMS calculation
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

                        # Stop condition 1: Silence after speech
                        if has_started_speaking and consecutive_silent_frames > SILENT_FRAMES_AFTER_SPEECH:
                            print("End of speech detected.")
                            break

                        # Stop condition 2: Timeout if no speech ever starts
                        if not has_started_speaking and len(audio_chunks) > SILENT_FRAMES_NO_SPEECH_TIMEOUT:
                            print("No speech detected, timing out.")
                            break

                        # Stop condition 3: Safety net for max recording length
                        if len(audio_chunks) > MAX_RECORDING_FRAMES:
                            print("Maximum recording time reached.")
                            break

                    # --- END DYNAMIC RECORDING ---

                    # Combine recorded chunks and convert to float32 for Whisper
                    audio_int16 = np.concatenate([chunk.flatten() for chunk in audio_chunks])
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

                    if intent['type'] == 'unknown' or intent['confidence'] < 0.75:
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
