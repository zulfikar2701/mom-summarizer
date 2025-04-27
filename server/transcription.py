import whisper

# load once at startup
model = whisper.load_model("small")  # CPU only

def transcribe_audio(path):
    # runs Whisper and returns the raw transcript
    result = model.transcribe(path)
    return result["text"]
