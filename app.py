import os
from flask import Flask, request, jsonify, render_template
import subprocess
from pytube import YouTube
from gtts import gTTS
import whisper
import tempfile
import logging

# Logging for Render debugging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

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
        audio_file = tempfile.mktemp(suffix=".mp4")
        stream.download(filename=audio_file)

        logging.info("Generating TTS audio...")
        tts = gTTS("Hello from AI subtitles!", lang='en')
        tts_audio = tempfile.mktemp(suffix=".mp3")
        tts.save(tts_audio)

        logging.info("Running Whisper transcription...")
        model = whisper.load_model("base")
        result = model.transcribe(tts_audio, word_timestamps=True)

        # Create subtitle file
        subs_file = tempfile.mktemp(suffix=".srt")
        with open(subs_file, "w") as f:
            for i, segment in enumerate(result["segments"], 1):
                start = segment["start"]
                end = segment["end"]
                text = segment["text"].strip()
                f.write(f"{i}\n")
                f.write(f"00:00:{start:05.2f} --> 00:00:{end:05.2f}\n")
                f.write(f"{text}\n\n")

        logging.info("Overlaying subtitles with FFmpeg...")
        output_video = tempfile.mktemp(suffix=".mp4")
        subprocess.run([
            "ffmpeg", "-y", "-i", audio_file, "-vf",
            f"subtitles={subs_file}:force_style='FontName=DejaVu Sans,FontSize=24,PrimaryColour=&HFFFFFF&'",
            "-c:a", "aac", output_video
        ], check=True)

        logging.info("Video generation complete.")
        return jsonify({"status": "success", "video_path": output_video})

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Render sets PORT
    app.run(host='0.0.0.0', port=port)
