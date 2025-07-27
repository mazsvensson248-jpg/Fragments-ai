from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from gtts import gTTS
from pytube import YouTube
import whisper
import os
import uuid
import re
import subprocess

app = Flask(__name__)
CORS(app)

# Create folders
os.makedirs("downloads", exist_ok=True)
os.makedirs("audio", exist_ok=True)
os.makedirs("output", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Load Whisper model once (base = smallest)
model = whisper.load_model("base")

def clean_text(text):
    return re.sub(r"[^a-zA-Z0-9,.?! ]", "", text)

def download_video(url):
    yt = YouTube(url)
    stream = yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc().first()
    filename = f"downloads/{uuid.uuid4().hex}.mp4"
    stream.download(output_path="downloads", filename=os.path.basename(filename))
    return filename

def generate_voice(prompt):
    path = f"audio/voice_{uuid.uuid4().hex}.mp3"
    gTTS(prompt).save(path)
    return path

def generate_subtitles(segments):
    filters = ""
    for seg in segments:
        for word in seg.get("words", []):
            txt = clean_text(word["word"])
            start = word["start"]
            end = word["end"]
            filters += f"drawtext=text='{txt}':fontcolor=white:fontsize=36:borderw=2:bordercolor=black:x=(w-text_w)/2:y=h-100:enable='between(t,{start},{end})',"
    return filters.rstrip(",")

@app.route("/")
def index():
    return send_file("static/index.html")

@app.route("/api/video", methods=["POST"])
def create_video():
    data = request.get_json()
    prompt = data.get("prompt")
    link = data.get("links", [None])[0]

    if not prompt or not link:
        return jsonify({"error": "Missing input"}), 400

    try:
        video = download_video(link)
        voice = generate_voice(prompt)
        result = model.transcribe(voice, word_timestamps=True)
        subs = generate_subtitles(result["segments"])
        output = f"output/out_{uuid.uuid4().hex}.mp4"

        cmd = [
            "ffmpeg", "-y",
            "-i", video, "-i", voice,
            "-filter_complex", subs,
            "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-c:a", "aac",
            "-shortest", output
        ]
        subprocess.run(cmd, check=True)

        return jsonify({"video": output})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
