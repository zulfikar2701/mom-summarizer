"""Meeting-transcript → bullet-point summary via a running vLLM server.

The vLLM server is expected to expose the *OpenAI-compatible* Chat API
(e.g. started with:
    python -m vllm.entrypoints.openai.api_server \
           --model google/gemma-2-2b-it --port 8001)

Environment variables you can tweak:
  VLLM_ENDPOINT   default: http://localhost:8001/v1/chat/completions
  LLM_MODEL       default: google/gemma-2-2b-it
"""

import os, json, requests
from typing import List

VLLM_ENDPOINT = os.getenv("VLLM_ENDPOINT",
                          "http://localhost:8001/v1/chat/completions")
LLM_MODEL     = os.getenv("LLM_MODEL", "google/gemma-2-2b-it")

SYSTEM_PROMPT = (
    "Adopt the role of an expert assistant skilled in synthesizing information. "
    "Your task is to create a concise yet thorough summary of meeting notes. "
    "This involves distilling the main points, decisions, action items, and next steps discussed during the meeting. "
    "The summary should be structured in a way that provides clarity and insight for someone who did not attend the meeting. "
    "Provide the summary in both English and Indonesian."
)

def _call_vllm(prompt: str, max_tokens: int = 256) -> str:
    resp = requests.post(
        VLLM_ENDPOINT,
        headers={"Content-Type": "application/json"},
        data=json.dumps({
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",
                 "content": f"Ringkas percakapan berikut menjadi poin-poin yang dapat dimengerti:\n\n{prompt}"}
            ],
            "temperature": 0,
            "max_tokens": max_tokens,
        }),
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()

def _split(text: str, size: int = 2000) -> List[str]:
    return [text[i:i+size] for i in range(0, len(text), size)]

def summarize_text(transcript: str) -> str:
    """Return newline-separated bullet list (markdown style)."""
    bullets = []
    for chunk in _split(transcript):
        bullets.append("- " + _call_vllm(chunk))
    return "\n".join(bullets)
