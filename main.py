from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from pytube import YouTube
from gtts import gTTS
import whisper
import subprocess
import os
import re
import uuid

app = Flask(__name__)
CORS(app)

def clean_for_ffmpeg(text):
    return re.sub(r"[^a-zA-Z0-9,.?! ]", "", text)

@app.route('/generate', methods=['POST'])
def generate_video():
    data = request.json
    youtube_url = data.get("youtube_url")
    prompt_text = data.get("prompt")

    if not youtube_url or not prompt_text:
        return jsonify({"error": "Missing YouTube URL or prompt"}), 400

    video = YouTube(youtube_url).streams.filter(file_extension='mp4').first()
    video_filename = f"video_{uuid.uuid4().hex}.mp4"
    video.download(filename=video_filename)

    tts = gTTS(text=prompt_text, lang="en")
    voice_file = f"voice_{uuid.uuid4().hex}.mp3"
    tts.save(voice_file)

    model = whisper.load_model("base")
    result = model.transcribe(voice_file, word_timestamps=True, language="en")
    segments = result["segments"]

    filters = ""
    for segment in segments:
        for word_info in segment.get("words", []):
            word = clean_for_ffmpeg(word_info["word"])
            start = word_info["start"]
            end = word_info["end"]
            filters += (
                f"drawtext=text='{word}':"
                f"fontsize=60:fontcolor=white:bordercolor=black:borderw=2:"
                f"x=(w-text_w)/2:y=(h-text_h)/2:"
                f"enable='between(t,{start},{end})',"
            )
    filters = filters.rstrip(",")

    output_file = f"final_{uuid.uuid4().hex}.mp4"
    cmd = f"""ffmpeg -y -i "{video_filename}" -i "{voice_file}" \
    -vf "{filters}" -map 0:v -map 1:a -c:v libx264 -c:a aac -shortest "{output_file}" """
    subprocess.call(cmd, shell=True)

    return send_file(output_file, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
