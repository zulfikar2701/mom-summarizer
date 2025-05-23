from pathlib import Path
import whisper
from vllm import LLM, SamplingParams


# ------------------------------------------------------------------
# 1.  whisper transcription
# ------------------------------------------------------------------
WHISPER_MODEL = whisper.load_model("turbo")


# ------------------------------------------------------------------
# 2.  lazy-initialised vLLM (spawn-safe)
# ------------------------------------------------------------------
_llm = None        # will be built on first use

_PARAMS = SamplingParams(
    temperature=0.0,
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
def transcribe_audio(wav_path: Path) -> str:
    """Run Whisper on an audio file and return raw transcript text."""
    result = WHISPER_MODEL.transcribe(str(wav_path))
    return result["text"]


def summarize_text(text: str) -> str:
    """Summarise a meeting based on the transcript text and have full understanding of the meeting context"""
    prompt = (
    "Adopt the role of an expert assistant skilled in synthesizing information. "
    "Your task is to create a concise yet thorough summary of meeting notes. "
    "This involves distilling the main points, decisions, action items, and next steps discussed during the meeting. "
    "The summary should be structured in a way that provides clarity and insight for someone who did not attend the meeting. "
    "Provide the summary in Indonesian.\n\n"
    "Keep the word context in mind and make sure to include all the important points.\n\n"
        f"{text}\n\nRingkasan:\n-"
    )
    llm = get_llm()
    out = llm.generate([prompt], _PARAMS)[0].outputs[0].text
    bullets = [
        "- " + line.lstrip("- ").strip()
        for line in out.splitlines()
        if line.strip()
    ]
    return "\n".join(bullets)


# ------------------------------------------------------------------
# 4.  public pipeline entry-point
# ------------------------------------------------------------------
def process_recording(wav_path: Path) -> tuple[str, str]:
    """Full pipeline → (transcript, summary)."""
    transcript = transcribe_audio(wav_path)
    summary    = summarize_text(transcript)
    return transcript, summary
