import os
import time
from flask import Flask, request, redirect, url_for, render_template, send_from_directory
from flask_login import login_required
from datetime import datetime

from auth import auth_bp, login_mgr
from models import db, Recording
from transcription import transcribe_audio
from summarization import summarize_text

def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config.update(
      SECRET_KEY="devkey",
      SQLALCHEMY_DATABASE_URI="sqlite:///data.db",
      UPLOAD_FOLDER="../recordings"
    )

    db.init_app(app)
    login_mgr.init_app(app)
    app.register_blueprint(auth_bp)

    @app.before_first_request
    def init_db():
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        db.create_all()

    @app.route("/")
    @login_required
    def index():
        recs = Recording.query.order_by(Recording.timestamp.desc()).all()
        return render_template("index.html", recordings=recs)

    @app.route("/upload", methods=["GET", "POST"])
    @login_required
    def upload():
        if request.method == "POST":
            f = request.files["audio"]
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            filename = f"{timestamp}_{f.filename}"
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            f.save(path)

            # Measure end-to-end processing time
            t0 = time.time()
            txt = transcribe_audio(path)
            summary = summarize_text(txt)
            print(f"[+] Total processing (transcribe+summarize): {time.time() - t0:.2f}s")

            rec = Recording(
                filename=filename,
                transcript=txt,
                summary=summary,
                timestamp=datetime.utcnow()
            )
            db.session.add(rec)
            db.session.commit()
            return redirect(url_for("index"))

        return render_template("upload.html")

    @app.route("/recordings/<filename>")
    @login_required
    def get_audio(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.route("/view/<int:id>")
    @login_required
    def view(id):
        r = Recording.query.get_or_404(id)
        return render_template("view.html", rec=r)

    return app

if __name__ == "__main__":
    app = create_app()
    app.config["DEBUG"] = True
    app.run(host="0.0.0.0", port=8000)
