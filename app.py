import os
import logging
import subprocess
from flask import Flask, request, jsonify, render_template
from pytube import YouTube
from gtts import gTTS
import whisper

# Logging to help debug on Render
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Preload Whisper model so it doesn't download mid-request
logging.info("Loading Whisper model...")
model = whisper.load_model("base")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/video', methods=['POST'])
def generate_video():
    data = request.json
    youtube_url = data.get("youtube_url")

    if not youtube_url:
        return jsonify({"status": "error", "message": "YouTube URL is required"}), 400

    try:
        logging.info(f"Downloading YouTube video: {youtube_url}")
        yt = YouTube(youtube_url)
        stream = yt.streams.filter(only_audio=True).first()
        audio_path = os.path.join("static", "videos", "input_audio.mp4")
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        stream.download(filename=audio_path)

        logging.info("Generating TTS audio...")
        tts = gTTS("Hello from AI subtitles!", lang='en')
        tts_audio = os.path.join("static", "videos", "tts_audio.mp3")
        tts.save(tts_audio)

        logging.info("Running Whisper transcription...")
        result = model.transcribe(tts_audio, word_timestamps=True)

        subs_file = os.path.join("static", "videos", "subtitles.srt")
        with open(subs_file, "w") as f:
            for i, segment in enumerate(result["segments"], 1):
                start = segment["start"]
                end = segment["end"]
                text = segment["text"].strip()
                f.write(f"{i}\n")
                f.write(f"00:00:{start:05.2f} --> 00:00:{end:05.2f}\n")
                f.write(f"{text}\n\n")

        logging.info("Overlaying subtitles with FFmpeg...")
        output_video = os.path.join("static", "videos", "output.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-i", audio_path, "-vf",
            f"subtitles={subs_file}:force_style='FontName=DejaVu Sans,FontSize=24,PrimaryColour=&HFFFFFF&'",
            "-c:a", "aac", output_video
        ], check=True)

        logging.info("Video generation complete.")
        return jsonify({
            "status": "success",
            "video_url": f"/static/videos/output.mp4"
        })

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Render will set PORT
    app.run(host='0.0.0.0', port=port)
