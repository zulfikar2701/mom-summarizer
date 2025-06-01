**BRP MOM Prototype Auto-Transcriber & Meeting Summarizer** 🚀

Lightweight CLI + web tool to record audio, transcribe with Whisper, and summarize with vLLM

---

## 📦 Prerequisites

Python 3.12+, FFmpeg, Git, (optional) virtualenv.

---

## ⚙️ Install

```bash
git clone
cd mom=summarizer
python3 -m venv .venv && source .venv/bin/activate  (Python 3.12 needed) # activate venv
pip install -r server/requirements.txt pydub sounddevice numpy argparse requests
```

(Optional) Rebuild CSS with Tailwind if you edit `input.css`.

---

## 🏃 Usage

**CLI Recorder**

```bash
python record.py --list      # list devices
python record.py             # record 5s
python record.py -d 15 -r 48000 -c 2  # custom
```

Saves `meeting-<timestamp>.mp3`.

**Upload Script**

```bash
python send_recording.py path/to/file.mp3
```

Use `API_URL`/`API_KEY` env vars.

**Web/API**

```bash
export SECRET_KEY=… API_KEY=…
python server/app.py
```

Browse `http://localhost:5000/` or use REST endpoints:

* `POST /api/v1/recordings` (multipart + X-API-Key)
* `GET /api/v1/recordings/<id>`

---

## 🚀 Deploy

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 server.app:app
```

Put behind Nginx (proxy to 8000). Set `SECRET_KEY`, `API_KEY`, `VLLM_ENDPOINT`, `LLM_MODEL` in env.

---

## 🔧 Structure

```
record.py        CLI recorder
send_recording.py Upload client
server/          Flask app & logic
.gitignore
```

---

## 🤝 Contributing

Open issues or PRs—MIT license.

✨ Enjoy automated meeting notes!
