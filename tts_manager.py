import io
import queue
import threading
import wave

import numpy as np
import sounddevice as sd

from tts import PiperTTSNative


class TTSManager:
    """
    Manages TTS synthesis and audio playback in a separate, non-blocking thread.
    """

    def __init__(self, tts_engine: PiperTTSNative):
        self.tts_engine = tts_engine
        self.task_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()

    def _play_audio(self, wav_bytes: bytes):
        """
        Plays WAV audio data from a byte string in a blocking manner,
        but this method itself is run in the worker thread.
        """
        if len(wav_bytes) <= 44:
            print("[TTSManager] ERROR: No valid audio data to play.")
            return

        try:
            with wave.open(io.BytesIO(wav_bytes), 'rb') as wav_file:
                sample_rate = wav_file.getframerate()
                num_channels = wav_file.getnchannels()
                samp_width = wav_file.getsampwidth()
                num_frames = wav_file.getnframes()

                raw_audio = wav_file.readframes(num_frames)

                dtype = np.int16 if samp_width == 2 else np.int32
                audio_data = np.frombuffer(raw_audio, dtype=dtype)

                print(f"[TTSManager] Playing {num_frames} frames at {sample_rate} Hz...")
                sd.play(audio_data, samplerate=sample_rate, blocking=True)
                print("[TTSManager] Playback finished.")

        except Exception as e:
            print(f"[TTSManager] ERROR: An error occurred during audio playback: {e}")

    def _process_queue(self):
        """
        The main loop for the worker thread. It waits for text to appear on the
        queue and then processes it.
        """
        while True:
            # This is a blocking call, the thread will wait here until a task is available
            text = self.task_queue.get()

            # A special "sentinel" value to signal the thread to exit
            if text is None:
                break

            print(f"[TTSManager] Worker thread received task: '{text}'")
            # Perform the slow, blocking operations here
            wav_bytes = self.tts_engine.speak(text)
            self._play_audio(wav_bytes)

            self.task_queue.task_done()

        print("[TTSManager] Worker thread shutting down.")

    def speak_async(self, text: str):
        """
        Public method to add text to the TTS queue. This is non-blocking.
        """
        if not text:
            return
        self.task_queue.put(text)
        print(f"[TTSManager] Queued for synthesis: '{text}'")

    def shutdown(self):
        """
        Shuts down the worker thread gracefully.
        """
        print("[TTSManager] Shutdown initiated.")
        # Signal the thread to exit by putting the sentinel on the queue
        self.task_queue.put(None)
        # Wait for the worker thread to finish its current task and exit
        self.worker_thread.join(timeout=5)
        print("[TTSManager] Shutdown complete.")
