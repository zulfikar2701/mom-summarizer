import os
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
    jsonify,
    abort,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

# ---------- basic Flask + SQLite setup ----------
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "recordings"
UPLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "devkey"),
    UPLOAD_FOLDER=str(UPLOAD_DIR),
    SQLALCHEMY_DATABASE_URI=f"sqlite:///{BASE_DIR/'db.sqlite3'}",
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

db = SQLAlchemy(app)

# ---------- models ----------
class Recording(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(256), nullable=False)
    transcript = db.Column(db.Text)
    summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ---------- business logic ----------
from transcription import process_recording  # noqa: E402  (import after db)

# ---------- HTML routes ----------
@app.route("/")
def index():
    recs = Recording.query.order_by(Recording.created_at.desc()).all()
    return render_template("index.html", recs=recs)


@app.route("/upload", methods=["POST"])
def upload_form():
    file = request.files["file"]
    if not file.filename.lower().endswith(".mp3"):
        return "Only .mp3 files are accepted", 400
    dest = UPLOAD_DIR / secure_filename(file.filename)
    file.save(dest)
    process_recording(dest)
    return redirect(url_for("index"))


@app.route("/recordings/<path:fname>")
def serve_audio(fname):
    return send_from_directory(app.config["UPLOAD_FOLDER"], fname)


# ---------- JSON API ----------
API_KEY = os.getenv("API_KEY")  # optional

@app.route("/api/v1/recordings", methods=["POST"])
def api_upload():
    # header-based key (swap for JWT/OAuth when you like)
    if API_KEY and request.headers.get("X-API-Key") != API_KEY:
        abort(401, description="bad or missing X-API-Key")

    if "file" not in request.files:
        return jsonify(error="missing file field"), 400
    f = request.files["file"]
    if not f.filename.lower().endswith(".mp3"):
        return jsonify(error="only .mp3 accepted"), 400

    dest = UPLOAD_DIR / secure_filename(f.filename)
    f.save(dest)
    rec = process_recording(dest)
    return jsonify(id=rec.id), 201


@app.route("/api/v1/recordings/<int:rec_id>")
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
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
