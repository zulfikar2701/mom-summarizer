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
        # ask for exactly one clear sentence, no bullets or numbering
        prompt = (
            "Adopt the role of an expert assistant skilled in synthesizing information. "
            "Your task is to create a concise yet thorough summary of meeting notes. "
            "This involves distilling the main points, decisions, action items, and next steps discussed during the meeting. "
            "The summary should be structured in a way that provides clarity and insight for someone who did not attend the meeting. "
            "Provide the summary in both English and Indonesian."
            "dalam bahasa Indonesia. Gunakan format bullet (-):\n\n"
            f"{seg}\n\nRingkasan:\n-"
        )
        out = llm.generate([prompt], _PARAMS)[0].outputs[0].text.strip()
        # keep only the first line in case the model spills multiple
        # avoid crashing if LLM returns an empty string
        lines = [l for l in out.splitlines() if l.strip()]
        if lines:
            first_line = lines[0].lstrip("- ").strip()
        else:
            # fallback to the first sentence of the raw segment text
            first_line = seg["text"].split(".", 1)[0].strip()
        bullets.append(f"[{ts}] {first_line}")
    return "\n".join(bullets)

# ------------------------------------------------------------------
# 4.  public pipeline entry-point
# ------------------------------------------------------------------
def process_recording(wav_path: Path) -> str:
    """Full pipeline: Whisper ➜ Gemma summary."""
    transcript, segments = transcribe_audio(wav_path)
    summary = summarize_segments(segments)
    return transcript, summary