# server/models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Recording(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    filename   = db.Column(db.String(256), nullable=False)
    transcript = db.Column(db.Text)
    summary    = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
