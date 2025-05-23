"""
mic_recorder.py
===============

A tiny voice-note recorder for Windows 10 / Python 3.12.

*  Records your default microphone.
*  Saves straight to MP3 as meeting-YYYYMMDD-HHMMSS.mp3.
*  Optional CLI flags: duration, samplerate, channels, list devices.

Usage examples
--------------
# default 5-second memo
py mic_recorder.py

# 15 seconds, stereo, 48 kHz
py mic_recorder.py -d 15 -c 2 -r 48000

# just show audio devices
py mic_recorder.py --list
"""

from __future__ import annotations

from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path

import numpy as np               # pulled in automatically with sounddevice
import sounddevice as sd
from pydub import AudioSegment


# --------------------------------------------------------------------------- #
# Core helpers
# --------------------------------------------------------------------------- #
def list_devices() -> None:
    """Print all PortAudio devices so you can pick a non-default mic."""
    print(sd.query_devices())


def record_to_mp3(duration: float, samplerate: int, channels: int) -> Path:
    """Capture audio from the default input and save as timestamped MP3."""
    total_frames = int(duration * samplerate)
    print(f"🎙️  Recording for {duration} s … Press Ctrl-C to cancel.")

    # Start capture (int16 = 16-bit PCM → 2 bytes per sample)
    audio: np.ndarray = sd.rec(
        total_frames,
        samplerate=samplerate,
        channels=channels,
        dtype="int16",
    )
    sd.wait()  # block until the buffer is full

    # Timestamped filename: meeting-YYYYMMDD-HHMMSS.mp3
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_file = Path(f"meeting-{stamp}.mp3")

    # Wrap raw PCM in a pydub AudioSegment
    segment = AudioSegment(
        audio.tobytes(),
        frame_rate=samplerate,
        sample_width=audio.dtype.itemsize,  # =2 for int16
        channels=channels,
    )

    # Export with a sensible bitrate (adjust if you like)
    segment.export(out_file, format="mp3", bitrate="192k")
    return out_file


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> ArgumentParser:
    p = ArgumentParser(description="Simple mic recorder that outputs MP3 files.")
    p.add_argument(
        "-d",
        "--duration",
        type=float,
        default=5.0,
        help="recording length in seconds (default: 5)",
    )
    p.add_argument(
        "-r",
        "--samplerate",
        type=int,
        default=44100,
        help="sample rate in Hz (default: 44100)",
    )
    p.add_argument(
        "-c",
        "--channels",
        type=int,
        default=1,
        choices=(1, 2),
        help="1 = mono, 2 = stereo (default: 1)",
    )
    p.add_argument(
        "--list",
        action="store_true",
        help="show available audio devices and exit",
    )
    return p


def main() -> None:
    args = build_parser().parse_args()

    if args.list:
        list_devices()
        return

    try:
        outfile = record_to_mp3(args.duration, args.samplerate, args.channels)
        print(f"✅  Saved voice note to: {outfile.resolve()}")
    except KeyboardInterrupt:
        print("\n❌  Recording cancelled.")
    except Exception as exc:
        print(f"❌  Error: {exc}")


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    main()
