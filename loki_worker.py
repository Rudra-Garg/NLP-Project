import os
import queue
import threading
from pathlib import Path

import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from faster_whisper import WhisperModel
from pvporcupine import create

from agent_manager import AgentManager
from agents import CalculationAgent, SystemControlAgent, VolumeControlAgent
from intent import FastClassifier, LLMClassifier
from ner_predictor import NERPredictor
from tts import PiperTTSNative
from tts_manager import TTSManager


class LokiWorker:
    """
    Encapsulates the entire LOKI voice assistant pipeline to be run in a background thread.
    Communicates with the main GUI thread via a queue.
    """

    def __init__(self, message_queue: queue.Queue, stop_event: threading.Event):
        self.queue = message_queue
        self.stop_event = stop_event
        self.porcupine = None
        self.tts_manager = None
        self.tts_engine = None

    def _initialize_components(self):
        """Loads all configuration and initializes LOKI components."""
        self.queue.put("STATUS: Loading configuration...")
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

        # Intent Classification
        INTENTS_JSON_PATH = os.environ.get("INTENTS_JSON_PATH")
        FAST_CLASSIFIER_MODEL = os.environ.get("FAST_CLASSIFIER_MODEL")
        FAST_CLASSIFIER_THRESHOLD = float(os.environ.get("FAST_CLASSIFIER_THRESHOLD", 0.80))
        OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "dolphin-phi")

        # Piper TTS
        PIPER_MODEL_PATH = os.environ.get("PIPER_MODEL_PATH")

        if not ACCESS_KEY:
            self.queue.put("ERROR: ACCESS_KEY not found in .env file.")
            return False

        self.queue.put("STATUS: Initializing LOKI components...")
        project_root = Path(__file__).parent

        porcupine_model_path = str(project_root / PORCUPINE_MODEL_PATH)
        porcupine_keyword_path = str(project_root / PORCUPINE_KEYWORD_PATH)
        intents_json_path = project_root / INTENTS_JSON_PATH
        piper_model_path = str(project_root / PIPER_MODEL_PATH)
        ner_model_path = project_root / "models" / "ner" / "ner_model.joblib"

        self.ner_predictor = NERPredictor(ner_model_path)
        self.porcupine = create(
            access_key=ACCESS_KEY,
            model_path=porcupine_model_path,
            keyword_paths=[porcupine_keyword_path],
            sensitivities=[PORCUPINE_SENSITIVITY]
        )

        self.queue.put(f"STATUS: Loading Whisper model '{WHISPER_MODEL_SIZE}'...")
        self.whisper = WhisperModel(WHISPER_MODEL_SIZE, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE_TYPE)

        self.fast_classifier = FastClassifier(
            intents_path=intents_json_path,
            model_name=FAST_CLASSIFIER_MODEL,
            threshold=FAST_CLASSIFIER_THRESHOLD
        )
        self.llm_classifier = LLMClassifier(model_name=OLLAMA_MODEL)

        self.agent_manager = AgentManager()
        self.agent_manager.register_agent(CalculationAgent())
        self.agent_manager.register_agent(SystemControlAgent())
        self.agent_manager.register_agent(VolumeControlAgent())

        self.tts_engine = PiperTTSNative(model_path=piper_model_path)
        self.tts_manager = TTSManager(tts_engine=self.tts_engine)

        return True

    def run(self):
        """The main loop of the voice assistant."""
        if not self._initialize_components():
            return

        SAMPLE_RATE, FRAME_LENGTH = self.porcupine.sample_rate, self.porcupine.frame_length

        self.queue.put("STATUS: Loki is online.")
        self.tts_manager.speak_async("Loki is online.")
        self.queue.put("STATUS: Listening for 'Hey Loki'...")

        try:
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', blocksize=FRAME_LENGTH) as stream:
                while not self.stop_event.is_set():
                    pcm, _ = stream.read(FRAME_LENGTH)
                    if self.porcupine.process(pcm.flatten()) >= 0:
                        self.queue.put("STATUS: Wake word detected!")
                        self.tts_manager.speak_async("Yes?")
                        # The rest of the processing logic from your main.py goes here
                        # Note the use of self.queue.put to send messages to the GUI
                        # instead of print()

                        # --- VAD and Recording Logic (Copied from main.py) ---
                        VAD_THRESHOLD = float(os.environ.get("VAD_THRESHOLD", 0.01))
                        VAD_SILENCE_FRAMES_AFTER_SPEECH = int(os.environ.get("VAD_SILENCE_FRAMES_AFTER_SPEECH", 40))
                        VAD_NO_SPEECH_TIMEOUT_FRAMES = int(os.environ.get("VAD_NO_SPEECH_TIMEOUT_FRAMES", 100))
                        VAD_MAX_RECORDING_FRAMES = int(os.environ.get("VAD_MAX_RECORDING_FRAMES", 350))

                        self.queue.put("STATUS: Listening for command...")
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
                                    self.queue.put("STATUS: Speech detected...")
                                    has_started_speaking = True
                                consecutive_silent_frames = 0
                            else:
                                if has_started_speaking:
                                    consecutive_silent_frames += 1
                            if has_started_speaking and consecutive_silent_frames > VAD_SILENCE_FRAMES_AFTER_SPEECH:
                                break
                            if not has_started_speaking and len(audio_chunks) > VAD_NO_SPEECH_TIMEOUT_FRAMES:
                                break
                            if len(audio_chunks) > VAD_MAX_RECORDING_FRAMES:
                                break
                        # --- End of VAD ---

                        audio_int16 = np.concatenate([c.flatten() for c in audio_chunks])
                        audio_float32 = audio_int16.astype(np.float32) / 32768.0

                        self.queue.put("STATUS: Transcribing...")
                        segments, _ = self.whisper.transcribe(audio_float32, language="en", vad_filter=True)
                        transcription = " ".join(s.text for s in segments).strip()

                        if not transcription:
                            self.queue.put("HEARD: Heard nothing.")
                            self.tts_manager.speak_async("I did not hear anything.")
                            self.queue.put("STATUS: Listening for 'Hey Loki'...")
                            continue

                        self.queue.put(f'HEARD: "{transcription}"')
                        intent = self.fast_classifier.classify(transcription)

                        if intent['type'] == 'unknown' or intent[
                            'confidence'] < self.fast_classifier.SIMILARITY_THRESHOLD:
                            self.queue.put("STATUS: Fast path failed. Falling back to LLM...")
                            intent = self.llm_classifier.classify(transcription)

                        if intent['type'] != 'unknown':
                            entities = self.ner_predictor.predict(transcription)
                            intent.setdefault('parameters', {}).update(entities)

                        response_text = self.agent_manager.dispatch(intent)
                        self.queue.put(f'LOKI: "{response_text}"')
                        self.tts_manager.speak_async(response_text)

                        self.queue.put("STATUS: Listening for 'Hey Loki'...")

        except Exception as e:
            self.queue.put(f"ERROR: An exception occurred: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleans up resources."""
        self.queue.put("STATUS: Shutting down...")
        if self.tts_manager:
            self.tts_manager.shutdown()
        if self.porcupine:
            self.porcupine.delete()
        if self.tts_engine:
            self.tts_engine.close()
        print("Loki Worker cleaned up resources.")
