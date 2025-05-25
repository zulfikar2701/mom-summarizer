from pathlib import Path
import whisper
from vllm import LLM, SamplingParams

# ------------------------------------------------------------------
# 0.  Timestamp helpers
# ------------------------------------------------------------------

def format_time(seconds: float) -> str:
    """Convert seconds to HH:MM:SS or MM:SS."""
    h, rem = divmod(int(seconds), 3600)
    m, s   = divmod(rem, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


# ------------------------------------------------------------------
# 1.  whisper transcription
# ------------------------------------------------------------------
WHISPER_MODEL = whisper.load_model("turbo")


# ------------------------------------------------------------------
# 2.  lazy-initialised vLLM (spawn-safe)
# ------------------------------------------------------------------
_llm = None        # will be built on first use

_PARAMS = SamplingParams(
    temperature=0.2,
    top_p=0.95,
    max_tokens=256,
)


def get_llm() -> LLM:
    """Create the vLLM engine only once, the first time it is needed."""
    global _llm
    if _llm is None:
        _llm = LLM(
            model="google/gemma-2-2b-it",
            dtype="bfloat16",
            gpu_memory_utilization=0.85,
            max_model_len=1024,
        )
    return _llm


# ------------------------------------------------------------------
# 3.  helpers
# ------------------------------------------------------------------
def transcribe_audio(wav_path: Path) -> tuple[str, list[dict]]:
    """Run Whisper on an audio file and return (text, segments)."""
    result = WHISPER_MODEL.transcribe(str(wav_path))
    return result["text"], result["segments"]

def summarize_segments(segments: list[dict]) -> str:
    """Summarise a long Indonesian transcript into bullet points."""
    llm = get_llm()
    bullets = []
    for seg in segments:
        ts = format_time(seg["start"])
        prompt = (
            "Ringkas teks berikut menjadi poin-poin penting yang singkat "
            "dalam bahasa Indonesia. Gunakan format bullet (-):\n\n"
            f"{seg}\n\nRingkasan:\n-"
        )
        out = llm.generate([prompt], _PARAMS)[0].outputs[0].text.strip()
        # strip any leading “– ” or bullets, then prefix timestamp
        summary_line = out.lstrip("- ").strip()
        bullets.append(f"[{ts}] {summary_line}")
    return "\n".join(bullets)

# ------------------------------------------------------------------
# 4.  public pipeline entry-point
# ------------------------------------------------------------------
def process_recording(wav_path: Path) -> str:
    """Full pipeline: Whisper ➜ Gemma summary."""
    transcript, segments = transcribe_audio(wav_path)
    summary = summarize_segments(segments)
    return transcript, summary