import os
import re
import tempfile
import subprocess
from pathlib import Path

from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS
from gtts import gTTS
import requests

# Lazy import of whisper to speed container start; load model on first use
_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        import whisper
        model_name = os.getenv("WHISPER_MODEL", "tiny")  # tiny is fast + RAM friendly on Render
        _whisper_model = whisper.load_model(model_name)
    return _whisper_model

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ----------- Utilities -----------

def clean_for_ffmpeg(text: str) -> str:
    # Keep basic punctuation; escape single quotes for drawtext
    text = re.sub(r"[^a-zA-Z0-9,.?! ]", "", text)
    return text.replace("'", r"\'")

def download_youtube_video_yt_dlp(url: str, out_dir: str) -> str:
    """
    Download a reasonable MP4 using yt-dlp, prefer <=720p to keep CPU/RAM reasonable.
    Returns the full path to the downloaded mp4.
    """
    from yt_dlp import YoutubeDL

    # Output template; yt-dlp will remux to mp4
    out_tmpl = str(Path(out_dir) / "video.%(ext)s")
    ydl_opts = {
        "format": "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "outtmpl": out_tmpl,
        "noprogress": True,
        "quiet": True,
        "retries": 3,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # Resolve output filename
        if "_filename" in info:
            return info["_filename"]
        # Fallback to expected.
        cand = Path(out_dir) / "video.mp4"
        return str(cand)

def build_drawtext_filter(words):
    """
    Build an ffmpeg drawtext filter with a **known font path** inside the container.
    DejaVuSans is available from fonts-dejavu-core.
    """
    fontfile = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    parts = []
    for w in words:
        word = clean_for_ffmpeg(w["word"])
        start = max(0.0, float(w["start"]))
        end = max(start, float(w["end"]))
        parts.append(
            "drawtext=fontfile='{font}':text='{text}':"
            "fontsize=48:fontcolor=white:bordercolor=black:borderw=2:"
            "x=(w-text_w)/2:y=(h-text_h)/2:enable='between(t,{start},{end})'"
            .format(font=fontfile, text=word, start=start, end=end)
        )
    return ",".join(parts)

# ----------- Routes -----------

@app.route("/", methods=["GET"])
def home():
    # Serve templates/index.html
    return render_template("index.html")

@app.route("/api/video", methods=["POST"])
def generate_video():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    links = data.get("links") or []

    if not prompt:
        return jsonify({"error": "Missing prompt"}), 400
    if not isinstance(links, list) or not (1 <= len(links) <= 10):
        return jsonify({"error": "Please provide 1..10 YouTube links"}), 400

    # Use only the first link for now (can be extended to montage later)
    link = links[0]

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # 1) Download video (mp4, <=720p)
            video_path = download_youtube_video_yt_dlp(link, tmpdir)
            if not os.path.exists(video_path):
                return jsonify({"error": "Failed to download video"}), 500

            # 2) Generate TTS audio from prompt
            tts_path = os.path.join(tmpdir, "voice.mp3")
            gTTS(text=prompt, lang="en").save(tts_path)

            # 3) Transcribe TTS audio with Whisper to get word timings
            model = get_whisper_model()
            result = model.transcribe(tts_path, word_timestamps=True, language="en", task="transcribe")
            segments = result.get("segments") or []
            words = []
            for seg in segments:
                for w in seg.get("words", []) or []:
                    # Ensure required keys exist
                    if "word" in w and "start" in w and "end" in w:
                        words.append({"word": w["word"], "start": w["start"], "end": w["end"]})

            if not words:
                return jsonify({"error": "No word-level timestamps from Whisper"}), 500

            # 4) Build drawtext filter with a known-good font path
            vf = build_drawtext_filter(words)

            # 5) Run ffmpeg to overlay subtitles and mux audio
            output_path = os.path.join(tmpdir, "final_video.mp4")
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", tts_path,
                "-vf", vf,
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-shortest",
                output_path
            ]
            run = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if run.returncode != 0 or not os.path.exists(output_path):
                return jsonify({
                    "error": "FFmpeg failed",
                    "details": run.stderr.decode(errors="ignore")[-4000:]  # last 4k for debugging
                }), 500

            return send_file(output_path, mimetype="video/mp4", as_attachment=True, download_name="generated_video.mp4")

        except Exception as e:
            return jsonify({"error": str(e)}), 500

# Secure server-side proxy for chat (no client-side key leaks)
@app.route("/api/chat", methods=["POST"])
def proxy_chat():
    """
    Frontend calls /api/chat; we forward to OpenRouter using a server-side API key.
    Set OPENROUTER_API_KEY in Render's Environment.
    """
    payload = request.get_json(silent=True) or {}
    messages = payload.get("messages") or []
    model = payload.get("model") or "openai/gpt-3.5-turbo"

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return jsonify({"error": "Server not configured with OPENROUTER_API_KEY"}), 500

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": os.getenv("APP_PUBLIC_URL", "https://example.com"),
                "X-Title": "FRAGMENTS AI Chat"
            },
            json={
                "model": model,
                "messages": messages
            },
            timeout=120,
        )
        return (resp.text, resp.status_code, resp.headers.items())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Useful for local dev; Render runs gunicorn
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
