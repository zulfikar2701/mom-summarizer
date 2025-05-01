import os
from datetime import datetime
from pathlib import Path

import torch
torch.backends.cuda.enable_flash_sdp(False)
torch.backends.cuda.enable_mem_efficient_sdp(False)
torch.backends.cuda.enable_math_sdp(True)

import whisper
from transformers import pipeline

from app import db, Recording   # models are defined in app.py

# ---------- model loading (done once at startup) ----------
WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL", "base")
whisper_model = whisper.load_model(WHISPER_MODEL_NAME)

SUMMARIZER_ID = os.getenv(
    "SUMMARIZER_ID", "cahya/t5-base-indonesian-summarization-cased"
)
summarizer = pipeline(
    "summarization",
    model=SUMMARIZER_ID,
    tokenizer=SUMMARIZER_ID,
    device=-1,            # CPU-only for the prototype
    use_fast=False,
)

# ---------- helper functions ----------
def transcribe_audio(filepath: Path) -> str:
    """Return plain-text transcript produced by Whisper."""
    result = whisper_model.transcribe(str(filepath))
    return result["text"].strip()


def summarize_text(text: str) -> str:
    """Chunk the transcript and build a bullet-point summary."""
    chunks = [text[i : i + 800] for i in range(0, len(text), 800)]
    bullets = []
    for c in chunks:
        s = summarizer(c, max_length=120, min_length=30, do_sample=False)[0][
            "summary_text"
        ]
        bullets.append(f"- {s.strip()}")
    return "\n".join(bullets)


def process_recording(filepath: Path) -> Recording:
    """Full pipeline: Whisper → summary → save row → return row."""
    transcript = transcribe_audio(filepath)
    summary = summarize_text(transcript)
    rec = Recording(
        filename=filepath.name,
        transcript=transcript,
        summary=summary,
    )   # created_at will be auto-filled
    db.session.add(rec)
    db.session.commit()
    return rec
