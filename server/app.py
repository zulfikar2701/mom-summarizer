import os
from datetime import datetime
from pathlib import Path
from flask import (Flask, render_template, request, redirect,
                   url_for, send_from_directory, jsonify, abort)
from werkzeug.utils import secure_filename

from models import db, Recording               # ← single source of truth
from transcription import process_recording    # noqa: E402

# ---------- basic Flask + SQLite setup ----------
BASE_DIR   = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "recordings"
UPLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "devkey"),
    UPLOAD_FOLDER=str(UPLOAD_DIR),
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{ (BASE_DIR / 'db.sqlite3').as_posix() }",
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

db.init_app(app)                               # DON’T create a new SQLAlchemy()

# ---------- HTML routes ----------
@app.get("/")
def index():
    recordings = Recording.query.order_by(Recording.created_at.desc()).all()
    return render_template("index.html", recordings=recordings,
                        current_year=datetime.utcnow().year)

@app.get("/upload")
def upload():
    return """
    <form action="/upload" method="post" enctype="multipart/form-data"
          class="flex flex-col gap-4 max-w-md mx-auto mt-10">
        <input type="file" name="file" accept=".mp3" class="border p-2 rounded">
        <button class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg">
            Send & transcribe
        </button>
    </form>
    """

@app.post("/upload")
def upload_post():
    file = request.files.get("file")
    if not file or not file.filename.lower().endswith(".mp3"):
        return "Only .mp3 files are accepted", 400

    dest = UPLOAD_DIR / secure_filename(file.filename)
    file.save(dest)

    # run Whisper ➜ Gemma
    transcript, summary = process_recording(dest)

    rec = Recording(
        filename   = file.filename,
        transcript = transcript,
        summary    = summary,
    )
    db.session.add(rec)
    db.session.commit()

    return redirect(url_for("index"))


@app.get("/download/<int:rec_id>")
def download_audio(rec_id):
    rec = db.session.get(Recording, rec_id) or abort(404)
    return send_from_directory(app.config["UPLOAD_FOLDER"], rec.filename)


@app.get("/recordings/<path:fname>")
def serve_audio(fname):
    return send_from_directory(app.config["UPLOAD_FOLDER"], fname)

# ---------- JSON API ----------
API_KEY = os.getenv("API_KEY")      # optional

@app.post("/api/v1/recordings")
def api_upload():
    if API_KEY and request.headers.get("X-API-Key") != API_KEY:
        abort(401, "bad or missing X-API-Key")

    f = request.files.get("file")
    if not f or not f.filename.lower().endswith(".mp3"):
        return jsonify(error="only .mp3 accepted"), 400

    dest = UPLOAD_DIR / secure_filename(f.filename)
    f.save(dest)

    transcript, summary = process_recording(dest)

    rec = Recording(filename=f.filename,
                    transcript=transcript,
                    summary=summary)
    db.session.add(rec)
    db.session.commit()

    return jsonify(id=rec.id), 201

@app.get("/api/v1/recordings/<int:rec_id>")
def api_get(rec_id):
    rec = Recording.query.get_or_404(rec_id)
    return jsonify(
        id=rec.id,
        filename=rec.filename,
        transcript=rec.transcript,
        summary=rec.summary,
        created_at=rec.created_at.isoformat() + "Z",
    )

# ---------- bootstrap ----------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()          # create tables once, only in the main process
    app.run(debug=False, host="0.0.0.0", port=5000)
