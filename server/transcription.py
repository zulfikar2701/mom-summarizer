# server/transcription.py
"""
Whisper → transcript → Indonesian T5 summary.
Called from app.py for both form and API uploads.
"""

# --- optional: work-around PyTorch flash-attention bug on CPU ---
import torch
torch.backends.cuda.enable_flash_sdp(False)
torch.backends.cuda.enable_mem_efficient_sdp(False)
torch.backends.cuda.enable_math_sdp(True)

# --- stdlib / third-party ---
from pathlib import Path
import whisper
from transformers import pipeline

# --- our database & model ---
from models import db, Recording            # SINGLE source of truth

# --- model loading (once at import time) ---
WHISPER_MODEL = whisper.load_model("turbo")  # or use env var
SUMMARIZER_ID = "cahya/t5-base-indonesian-summarization-cased"
summarizer = pipeline(
    "summarization",
    model=SUMMARIZER_ID,
    tokenizer=SUMMARIZER_ID,
    device=-1,
    use_fast=False,
)

# --- helper functions ---
def transcribe_audio(path: Path) -> str:
    """Return plaintext transcript produced by Whisper."""
    result = WHISPER_MODEL.transcribe(str(path))
    return result["text"].strip()

def summarize_text(text: str) -> str:
    chunks  = [text[i : i + 800] for i in range(0, len(text), 800)]
    bullets = [
        "- " + summarizer(c, max_length=120, min_length=30, do_sample=False)[0]["summary_text"].strip()
        for c in chunks
    ]
    return "\n".join(bullets)

def process_recording(path: Path) -> Recording:
    """Full pipeline: transcribe, summarise, write DB row, return it."""
    transcript = transcribe_audio(path)
    summary    = summarize_text(transcript)

    rec = Recording(
        filename   = path.name,
        transcript = transcript,
        summary    = summary,
        # created_at auto-filled by column default
    )
    db.session.add(rec)
    db.session.commit()
    return rec
