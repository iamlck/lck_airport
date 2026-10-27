import base64
from fastapi import APIRouter, UploadFile, File
from lck_backend.schemas.audio import TranscriptionResponse, SynthesisRequest, SynthesisResponse, VisemeCue

router = APIRouter(prefix="/audio", tags=["Audio (STT/TTS)"])


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribes uploaded audio (WAV/WebM) into text.
    Uses lightweight mock/faster-whisper integration.
    """
    audio_bytes = await file.read()
    # In full deployment, faster-whisper / Whisper model transcribes here
    # Fallback/mock for offline zero-cloud test
    return TranscriptionResponse(
        text="Where is the lounge in Terminal 2?",
        detected_language="en",
        duration_seconds=2.4,
        confidence=0.98
    )


@router.post("/synthesize", response_model=SynthesisResponse)
async def synthesize_speech(request: SynthesisRequest):
    """
    Synthesizes text into speech and returns base64 audio and phoneme-to-viseme cues.
    """
    # Sample viseme cues mapped to word lengths
    visemes = [
        VisemeCue(time_ms=0, viseme="viseme_sil"),
        VisemeCue(time_ms=100, viseme="viseme_aa"),
        VisemeCue(time_ms=250, viseme="viseme_E"),
        VisemeCue(time_ms=450, viseme="viseme_O"),
        VisemeCue(time_ms=700, viseme="viseme_sil"),
    ]
    # Return 1 second of empty WAV container header or mock audio base64
    fake_wav_bytes = b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    b64_audio = base64.b64encode(fake_wav_bytes).decode("utf-8")

    return SynthesisResponse(
        audio_base64=b64_audio,
        audio_format="wav",
        language=request.language,
        duration_ms=1000,
        visemes=visemes
    )

