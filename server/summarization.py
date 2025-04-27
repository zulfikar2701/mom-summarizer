from transformers import pipeline

model_id = "cahya/t5-base-indonesian-summarization-cased"
summarizer = pipeline(
    "summarization",
    model=model_id,
    tokenizer=model_id,
    device=-1,
    use_fast=False   # if you didn’t install protobuf
)

def summarize_text(text: str) -> str:
    # split into ~800-char chunks
    chunks = [ text[i:i+800] for i in range(0, len(text), 800) ]
    bullets = []
    for chunk in chunks:
        out = summarizer(
            chunk,
            max_length=120,
            min_length=30,
            do_sample=False
        )[0]["summary_text"]
        bullets.append(f"- {out.strip()}")
    return "\n".join(bullets)
