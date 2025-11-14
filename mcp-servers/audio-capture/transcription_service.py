"""Real-time audio transcription service using faster-whisper

This module provides real-time speech-to-text transcription with VAD.
"""
import logging
import queue
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import pyaudio

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

try:
    import webrtcvad
except ImportError:
    webrtcvad = None

from shared.models.audio_transcript import AudioTranscript

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Real-time audio transcription with VAD

    This service:
    - Captures audio from microphone
    - Uses VAD to filter silence
    - Transcribes speech in real-time using faster-whisper
    - Provides streaming transcription results
    """

    def __init__(
        self,
        model_size: str = "base.en",
        language: str = "en",
        vad_mode: int = 3,
        sample_rate: int = 16000,
        chunk_duration_ms: int = 30,
        device: str = "cpu",
    ):
        """Initialize transcription service

        Args:
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
            language: Language code (e.g., 'en')
            vad_mode: VAD aggressiveness (0-3, 3 is most aggressive)
            sample_rate: Audio sample rate in Hz (must be 8000, 16000, 32000, or 48000)
            chunk_duration_ms: Audio chunk duration in milliseconds (10, 20, or 30)
            device: Device for inference ('cpu' or 'cuda')
        """
        if WhisperModel is None:
            raise ImportError("faster-whisper not installed. Install with: pip install faster-whisper")

        if webrtcvad is None:
            raise ImportError("webrtcvad not installed. Install with: pip install webrtcvad")

        self.model_size = model_size
        self.language = language
        self.vad_mode = vad_mode
        self.sample_rate = sample_rate
        self.chunk_duration_ms = chunk_duration_ms
        self.device = device

        # Audio configuration
        self.chunk_size = int(sample_rate * chunk_duration_ms / 1000)
        self.format = pyaudio.paInt16
        self.channels = 1

        # State
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.transcript_callback: Optional[Callable[[AudioTranscript], None]] = None

        # Initialize components (lazy loading)
        self.whisper_model: Optional[WhisperModel] = None
        self.vad: Optional[webrtcvad.Vad] = None
        self.audio_interface: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None

        # Threading
        self.capture_thread: Optional[threading.Thread] = None
        self.transcription_thread: Optional[threading.Thread] = None

        # Buffer for VAD
        self.speech_buffer = []
        self.silence_chunks = 0
        self.max_silence_chunks = 30  # ~1 second of silence to end utterance

    def _init_components(self):
        """Initialize Whisper model, VAD, and audio interface"""
        if self.whisper_model is None:
            logger.info(f"Loading Whisper model: {self.model_size}")
            self.whisper_model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type="int8" if self.device == "cpu" else "float16",
            )
            logger.info("Whisper model loaded")

        if self.vad is None:
            self.vad = webrtcvad.Vad(self.vad_mode)
            logger.info(f"VAD initialized with mode {self.vad_mode}")

        if self.audio_interface is None:
            self.audio_interface = pyaudio.PyAudio()
            logger.info("Audio interface initialized")

    def start_listening(self, callback: Callable[[AudioTranscript], None]):
        """Start real-time transcription

        Args:
            callback: Function to call with each transcription result
        """
        if self.is_listening:
            logger.warning("Already listening")
            return

        self._init_components()
        self.transcript_callback = callback
        self.is_listening = True

        # Start audio capture thread
        self.capture_thread = threading.Thread(target=self._capture_audio, daemon=True)
        self.capture_thread.start()

        # Start transcription thread
        self.transcription_thread = threading.Thread(target=self._process_audio, daemon=True)
        self.transcription_thread.start()

        logger.info("Started listening")

    def stop_listening(self):
        """Stop real-time transcription"""
        if not self.is_listening:
            logger.warning("Not currently listening")
            return

        self.is_listening = False

        # Wait for threads to finish
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
        if self.transcription_thread:
            self.transcription_thread.join(timeout=2)

        # Close audio stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        logger.info("Stopped listening")

    def _capture_audio(self):
        """Capture audio from microphone (runs in separate thread)"""
        try:
            self.stream = self.audio_interface.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
            )

            logger.info("Audio stream opened")

            while self.is_listening:
                try:
                    data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                    self.audio_queue.put(data)
                except Exception as e:
                    logger.error(f"Error reading audio: {e}")
                    break

        except Exception as e:
            logger.error(f"Error in audio capture: {e}")
            self.is_listening = False

    def _process_audio(self):
        """Process audio queue and transcribe (runs in separate thread)"""
        while self.is_listening:
            try:
                # Get audio chunk from queue
                try:
                    audio_chunk = self.audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                # Check if speech is present using VAD
                is_speech = self._is_speech(audio_chunk)

                if is_speech:
                    self.speech_buffer.append(audio_chunk)
                    self.silence_chunks = 0
                elif len(self.speech_buffer) > 0:
                    self.silence_chunks += 1

                    # If enough silence, process the buffered speech
                    if self.silence_chunks >= self.max_silence_chunks:
                        self._transcribe_buffer()
                        self.speech_buffer = []
                        self.silence_chunks = 0

            except Exception as e:
                logger.error(f"Error processing audio: {e}")

        # Process any remaining buffer
        if len(self.speech_buffer) > 0:
            self._transcribe_buffer()

    def _is_speech(self, audio_chunk: bytes) -> bool:
        """Check if audio chunk contains speech using VAD

        Args:
            audio_chunk: Audio data as bytes

        Returns:
            True if speech is detected, False otherwise
        """
        try:
            return self.vad.is_speech(audio_chunk, self.sample_rate)
        except Exception as e:
            logger.error(f"VAD error: {e}")
            return False

    def _transcribe_buffer(self):
        """Transcribe buffered audio"""
        if not self.speech_buffer:
            return

        try:
            # Combine audio chunks
            audio_data = b"".join(self.speech_buffer)

            # Convert to numpy array
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

            # Skip if audio is too short
            if len(audio_np) < self.sample_rate * 0.5:  # Less than 0.5 seconds
                return

            # Transcribe
            segments, info = self.whisper_model.transcribe(
                audio_np,
                language=self.language,
                beam_size=5,
                vad_filter=False,  # We already did VAD
            )

            # Combine segments into full text
            text_parts = []
            avg_confidence = 0
            segment_count = 0

            for segment in segments:
                text_parts.append(segment.text)
                # Note: faster-whisper doesn't provide confidence per segment
                # We can use the probability field if available
                segment_count += 1

            if text_parts:
                text = " ".join(text_parts).strip()

                if text:
                    # Create transcript
                    transcript = AudioTranscript(
                        timestamp=datetime.now().isoformat(),
                        source="microphone",
                        text=text,
                        speaker="user",
                        confidence=None,  # faster-whisper doesn't provide this
                        metadata={
                            "model": self.model_size,
                            "language": info.language,
                            "language_probability": info.language_probability,
                            "duration": info.duration,
                        },
                    )

                    # Call callback
                    if self.transcript_callback:
                        self.transcript_callback(transcript)

                    logger.info(f"Transcribed: {text}")

        except Exception as e:
            logger.error(f"Transcription error: {e}")

    def cleanup(self):
        """Clean up resources"""
        self.stop_listening()

        if self.audio_interface:
            self.audio_interface.terminate()
            self.audio_interface = None

        logger.info("Cleanup complete")


__all__ = ["TranscriptionService"]
