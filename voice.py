"""
voice.py — Voice command system.

Primary STT: SpeechRecognition library (uses Google Web Speech API by default,
             works offline with sphinx fallback).
Optional:    whisper (OpenAI's tiny local model, 39MB, fully offline)

Flow:
  VoiceListener runs in a background thread.
  On wake word detection ("hey buddy" / "okay dog" / configurable),
  it records the command, transcribes it, then calls the command_callback.

Wake words are checked locally (no API).
Command transcription uses the best available engine.

Usage:
    vl = VoiceListener(wake_words=["hey buddy","okay dog"])
    vl.on_command = lambda text: ...
    vl.start()
    vl.stop()
"""

import threading
import queue
import time


WAKE_WORDS = ["hey buddy", "okay dog", "hey dog", "buddy", "hey pet"]

# Per-pet-type default wake words
PET_WAKE_WORDS = {
    "dog":    ["hey buddy", "okay dog", "hey dog", "buddy"],
    "dragon": ["hey dragon", "okay dragon", "dragon", "hey buddy"],
    "cat":    ["hey kitty", "hey cat", "okay kitty", "kitty", "hey buddy"],
}

# Energy threshold for ambient noise (auto-calibrated on start)
ENERGY_THRESHOLD = 300


class VoiceListener:
    def __init__(self, wake_words=None, command_callback=None):
        self.wake_words       = [w.lower() for w in (wake_words or WAKE_WORDS)]
        self.on_command       = command_callback    # fn(text: str)
        self.on_wake          = None               # fn() — called on wake word
        self.on_error         = None               # fn(err: str)
        self._running         = False
        self._thread          = None
        self._sr_available    = False
        self._whisper_available = False
        self._command_q       = queue.Queue()
        self._check_deps()

    def _check_deps(self):
        try:
            import speech_recognition as sr  # noqa
            self._sr_available = True
        except ImportError:
            pass
        try:
            import whisper  # type: ignore  # optional
            self._whisper_available = True
        except ImportError:
            pass

    @property
    def is_available(self):
        return self._sr_available or self._whisper_available

    def start(self):
        if not self.is_available:
            print("[voice] No STT available.")
            print("        Install: pip install SpeechRecognition pyaudio")
            print("        Or:      pip install openai-whisper")
            return False
        self._running = True
        self._thread  = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        print(f"[voice] Listening... wake words: {self.wake_words}")
        return True

    def stop(self):
        self._running = False

    # ── Main listen loop ─────────────────────────────────────────────────

    def _listen_loop(self):
        if self._sr_available:
            self._sr_loop()
        elif self._whisper_available:
            self._whisper_loop()

    def _sr_loop(self):
        import speech_recognition as sr
        rec = sr.Recognizer()
        rec.energy_threshold  = ENERGY_THRESHOLD
        rec.dynamic_energy_threshold = True
        rec.pause_threshold   = 0.8

        with sr.Microphone() as source:
            print("[voice] Calibrating for ambient noise...")
            rec.adjust_for_ambient_noise(source, duration=1.5)
            print(f"[voice] Ready. Energy threshold: {rec.energy_threshold:.0f}")

            while self._running:
                try:
                    # Listen for audio
                    audio = rec.listen(source, timeout=5, phrase_time_limit=6)
                    # Transcribe
                    try:
                        text = rec.recognize_google(audio).lower().strip()
                    except sr.UnknownValueError:
                        continue
                    except sr.RequestError:
                        # Fallback to sphinx if Google unavailable
                        try:
                            text = rec.recognize_sphinx(audio).lower().strip()
                        except Exception:
                            continue

                    print(f"[voice] Heard: '{text}'")
                    self._process(text)

                except sr.WaitTimeoutError:
                    continue
                except Exception as e:
                    if self._running:
                        print(f"[voice] Error: {e}")
                    time.sleep(0.5)

    def _whisper_loop(self):
        """Whisper-based loop — fully offline, more accurate but slower."""
        import whisper       # type: ignore  # optional: pip install openai-whisper
        import sounddevice as sd  # type: ignore  # optional: pip install sounddevice

        print("[voice] Loading Whisper tiny model...")
        model = whisper.load_model("tiny")
        print("[voice] Whisper ready.")

        SAMPLE_RATE = 16000
        CHUNK       = 1024
        SILENCE_SEC = 1.5   # stop recording after this silence

        while self._running:
            # Simple VAD: record until silence
            frames = []
            recording = False
            silent_chunks = 0
            silent_limit = int(SILENCE_SEC * SAMPLE_RATE / CHUNK)

            def callback(indata, frame_count, time_info, status):
                nonlocal recording, silent_chunks
                amplitude = max(abs(x) for x in indata.flatten())
                if amplitude > 0.01:
                    recording = True
                    silent_chunks = 0
                    frames.extend(indata.flatten().tolist())
                elif recording:
                    silent_chunks += 1
                    frames.extend(indata.flatten().tolist())

            with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                                 callback=callback, blocksize=CHUNK):
                while self._running and silent_chunks < silent_limit:
                    time.sleep(0.1)

            if not frames or len(frames) < SAMPLE_RATE // 2:
                continue

            # Write to temp wav, transcribe
            try:
                import numpy as np
                audio_data = np.array(frames, dtype=np.float32)
                result = model.transcribe(audio_data, language="en",
                                          fp16=False, verbose=False)
                text = result["text"].lower().strip()
                if text:
                    print(f"[voice] Heard: '{text}'")
                    self._process(text)
            except Exception as e:
                print(f"[voice] Whisper error: {e}")

    # ── Command processing ────────────────────────────────────────────────

    def _process(self, text: str):
        """Check for wake word, then fire command callback."""
        # Check if text contains a wake word
        has_wake = any(w in text for w in self.wake_words)

        if has_wake:
            # Strip wake word from command
            command = text
            for w in self.wake_words:
                command = command.replace(w, "").strip(" ,.")
            if self.on_wake:
                self.on_wake()
            if command and self.on_command:
                self.on_command(command)
            elif self.on_command:
                # Just the wake word alone = say hi
                self.on_command("hello")
        else:
            # No wake word — ignore (background noise)
            pass

    # ── Text input fallback (for testing without mic) ─────────────────────

    def send_text_command(self, text: str):
        """Inject a text command directly (useful for testing/tray input)."""
        if self.on_command:
            self.on_command(text.lower().strip())