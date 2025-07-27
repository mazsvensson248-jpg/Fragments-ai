from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from gtts import gTTS
from pytube import YouTube
import whisper
import ffmpeg
import os
import re
import uuid

# Create necessary directories
os.makedirs("downloads", exist_ok=True)
os.makedirs("audio", exist_ok=True)
os.makedirs("output", exist_ok=True)
os.makedirs("static", exist_ok=True)

app = Flask(__name__)
CORS(app)

# Load Whisper model
model = whisper.load_model("base")

def clean_for_ffmpeg(text):
    return re.sub(r"[^a-zA-Z0-9,.?! ]", "", text)

def download_youtube_video(url):
    yt = YouTube(url)
    stream = yt.streams.filter(file_extension='mp4', progressive=True).order_by('resolution').desc().first()
    if not stream:
        raise Exception("No suitable video stream found.")
    filename = f"downloads/{uuid.uuid4().hex}.mp4"
    stream.download(output_path="downloads", filename=os.path.basename(filename))
    return filename

def generate_voice_audio(prompt):
    filename = f"audio/voice_{uuid.uuid4().hex}.mp3"
    tts = gTTS(text=prompt, lang="en")
    tts.save(filename)
    return filename

def generate_subtitle_filters(segments):
    filters = ""
    for segment in segments:
        for word_info in segment.get("words", []):
            word = clean_for_ffmpeg(word_info["word"])
            start = word_info["start"]
            end = word_info["end"]
            filters += (
                f"drawtext=text='{word}':fontcolor=white:fontsize=48:borderw=2:bordercolor=black:"
                f"x=(w-text_w)/2:y=h-100:enable='between(t,{start},{end})',"
            )
    return filters.rstrip(',')

@app.route("/")
def index():
    return send_file("static/index.html")

@app.route("/api/video", methods=["POST"])
def generate_video():
    data = request.get_json()
    prompt = data.get("prompt")
    links = data.get("links", [])

    if not prompt or not links:
        return jsonify({"error": "Missing prompt or video links"}), 400

    try:
        video_path = download_youtube_video(links[0])
        voice_path = generate_voice_audio(prompt)

        result = model.transcribe(voice_path, word_timestamps=True, language="en")
        segments = result.get("segments", [])
        if not segments:
            raise Exception("Whisper transcription failed.")

        subtitle_filter = generate_subtitle_filters(segments)
        output_path = f"output/final_{uuid.uuid4().hex}.mp4"
        ffmpeg_cmd = (
            f"./ffmpeg -y -i {video_path} -i {voice_path} -filter_complex \"{subtitle_filter}\" "
            f"-map 0:v -map 1:a -c:v libx264 -c:a aac -b:a 192k -shortest {output_path}"
        )
        result = os.system(ffmpeg_cmd)
        if result != 0 or not os.path.exists(output_path):
            raise Exception("FFmpeg failed to generate final video.")

        return jsonify({"video": output_path})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
