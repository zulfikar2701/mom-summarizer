import os
import time
import whisper
import whisper.audio as wa

os.environ["PATH"] = r"C:\ProgramData\chocolatey\bin" + os.pathsep + os.environ.get("PATH", "")

model = whisper.load_model("turbo")  # choose "base" or "medium" if you have more CPU power

def transcribe_audio(path: str) -> str:
    # load  duration log (unchanged)
    start_load = time.time()
    audio = wa.load_audio(path)
    rec_dur = len(audio) / wa.SAMPLE_RATE
    print(f"[] Recording duration: {rec_dur:.2f}s (loaded in {time.time() - start_load:.2f}s)")

    # now force Whisper to transcribe in Indonesian
    start_trans = time.time()
    result = model.transcribe(
        path,
        language="id",      # ← force output to Bahasa Indonesia
        task="transcribe"   # ← default, but explicit is clearer
    )
    trans_time = time.time() - start_trans
    print(f"[] Transcription took: {trans_time:.2f}s")

    return result["text"]