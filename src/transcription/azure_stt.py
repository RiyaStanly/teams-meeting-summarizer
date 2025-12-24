"""Azure Speech-to-Text integration for real-time transcription."""

from typing import Callable, Optional

try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    speechsdk = None

from src.config import settings
from src.utils.logger import logger


class AzureSpeechTranscriber:
    """Real-time audio transcription using Azure Cognitive Services."""

    def __init__(
        self,
        on_transcribed: Optional[Callable[[str, bool], None]] = None,
        on_speaker_detected: Optional[Callable[[str, int], None]] = None,
    ):
        """
        Initialize Azure Speech transcriber.

        Args:
            on_transcribed: Callback for transcribed text (text, is_final)
            on_speaker_detected: Callback for speaker detection (text, speaker_id)
        """
        if speechsdk is None:
            raise ImportError(
                "Azure Speech SDK not installed. "
                "Install with: pip install azure-cognitiveservices-speech"
            )

        if not settings.azure_speech_key:
            raise ValueError(
                "Azure Speech key not configured. "
                "Set AZURE_SPEECH_KEY in environment or .env file"
            )

        self.on_transcribed = on_transcribed
        self.on_speaker_detected = on_speaker_detected

        # Configure speech service
        speech_config = speechsdk.SpeechConfig(
            subscription=settings.azure_speech_key, region=settings.azure_speech_region
        )

        # Set recognition language
        speech_config.speech_recognition_language = settings.azure_speech_language

        # Enable interim results
        speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceResponse_RequestWordLevelTimestamps, "true"
        )

        # Enable speaker diarization if configured
        if settings.azure_speech_enable_diarization:
            speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceResponse_DiarizeIntermediateResults,
                "true",
            )

        # Use default microphone
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

        # Create recognizer
        self.recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config, audio_config=audio_config
        )

        # Setup event handlers
        self._setup_event_handlers()

        logger.info("Azure Speech transcriber initialized")

    def _setup_event_handlers(self):
        """Setup event handlers for recognition events."""

        def recognizing_cb(evt):
            """Handle interim recognition results."""
            if self.on_transcribed:
                text = evt.result.text
                self.on_transcribed(text, is_final=False)
            logger.debug(f"Recognizing: {evt.result.text}")

        def recognized_cb(evt):
            """Handle final recognition results."""
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                text = evt.result.text
                if self.on_transcribed:
                    self.on_transcribed(text, is_final=True)

                # Extract speaker info if available
                if settings.azure_speech_enable_diarization:
                    speaker_id = evt.result.speaker_id
                    if self.on_speaker_detected:
                        self.on_speaker_detected(text, speaker_id)

                logger.info(f"Recognized: {text}")
            elif evt.result.reason == speechsdk.ResultReason.NoMatch:
                logger.warning("No speech could be recognized")

        def canceled_cb(evt):
            """Handle recognition cancellation."""
            if evt.reason == speechsdk.CancellationReason.Error:
                logger.error(f"Recognition canceled: {evt.error_details}")
            else:
                logger.info("Recognition canceled")

        # Connect callbacks
        self.recognizer.recognizing.connect(recognizing_cb)
        self.recognizer.recognized.connect(recognized_cb)
        self.recognizer.canceled.connect(canceled_cb)

    def start_continuous_recognition(self):
        """Start continuous recognition from microphone."""
        logger.info("Starting continuous recognition...")
        self.recognizer.start_continuous_recognition()

    def stop_continuous_recognition(self):
        """Stop continuous recognition."""
        logger.info("Stopping continuous recognition...")
        self.recognizer.stop_continuous_recognition()

    @staticmethod
    def transcribe_audio_file(audio_file_path: str) -> str:
        """
        Transcribe an audio file.

        Args:
            audio_file_path: Path to audio file (WAV, MP3, etc.)

        Returns:
            Transcribed text
        """
        if speechsdk is None:
            raise ImportError("Azure Speech SDK not installed")

        if not settings.azure_speech_key:
            raise ValueError("Azure Speech key not configured")

        logger.info(f"Transcribing audio file: {audio_file_path}")

        # Configure speech service
        speech_config = speechsdk.SpeechConfig(
            subscription=settings.azure_speech_key, region=settings.azure_speech_region
        )
        speech_config.speech_recognition_language = settings.azure_speech_language

        # Configure audio input
        audio_config = speechsdk.audio.AudioConfig(filename=audio_file_path)

        # Create recognizer
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config, audio_config=audio_config
        )

        # Perform recognition
        result = recognizer.recognize_once()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            logger.info(f"Transcription complete: {len(result.text)} characters")
            return result.text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            logger.warning("No speech could be recognized")
            return ""
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            logger.error(f"Recognition canceled: {cancellation.reason}")
            if cancellation.reason == speechsdk.CancellationReason.Error:
                logger.error(f"Error details: {cancellation.error_details}")
            return ""

        return ""

    @staticmethod
    def transcribe_audio_file_continuous(
        audio_file_path: str, on_partial: Optional[Callable[[str], None]] = None
    ) -> str:
        """
        Transcribe an audio file with continuous recognition.

        Args:
            audio_file_path: Path to audio file
            on_partial: Optional callback for partial results

        Returns:
            Complete transcribed text
        """
        if speechsdk is None:
            raise ImportError("Azure Speech SDK not installed")

        if not settings.azure_speech_key:
            raise ValueError("Azure Speech key not configured")

        logger.info(f"Transcribing audio file (continuous): {audio_file_path}")

        # Configure speech service
        speech_config = speechsdk.SpeechConfig(
            subscription=settings.azure_speech_key, region=settings.azure_speech_region
        )
        speech_config.speech_recognition_language = settings.azure_speech_language

        # Configure audio input
        audio_config = speechsdk.audio.AudioConfig(filename=audio_file_path)

        # Create recognizer
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config, audio_config=audio_config
        )

        # Collect all recognized text
        all_text = []
        done = False

        def recognized_cb(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                text = evt.result.text
                all_text.append(text)
                if on_partial:
                    on_partial(text)

        def stop_cb(evt):
            nonlocal done
            done = True

        # Connect callbacks
        recognizer.recognized.connect(recognized_cb)
        recognizer.session_stopped.connect(stop_cb)
        recognizer.canceled.connect(stop_cb)

        # Start recognition
        recognizer.start_continuous_recognition()

        # Wait for completion
        import time

        while not done:
            time.sleep(0.5)

        recognizer.stop_continuous_recognition()

        complete_text = " ".join(all_text)
        logger.info(f"Transcription complete: {len(complete_text)} characters")

        return complete_text
