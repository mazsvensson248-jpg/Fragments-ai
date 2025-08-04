from flask import Flask, render_template, request, jsonify, send_file
import os
import tempfile
import requests
from werkzeug.exceptions import BadRequest

# Added imports
import uuid
import re
import whisper
from pytube import YouTube
from gtts import gTTS
import subprocess

app = Flask(__name__)

# Load Whisper model once
whisper_model = whisper.load_model("base")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/video', methods=['POST'])
def generate_video():
    try:
        data = request.get_json()

        if not data:
            raise BadRequest("No JSON data provided")

        prompt = data.get('prompt', '').strip()
        links = data.get('links', [])

        if not prompt:
            raise BadRequest("Prompt is required")

        if not links or len(links) > 10:
            raise BadRequest("Please provide between 1 and 10 video links")

        # === ADDED FUNCTIONALITY STARTS HERE === #
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download first YouTube video
            yt = YouTube(links[0])
            stream = yt.streams.filter(file_extension="mp4", progressive=True).order_by("resolution").desc().first()
            video_path = os.path.join(temp_dir, "video.mp4")
            stream.download(filename=video_path)

            # Extract audio
            audio_path = os.path.join(temp_dir, "audio.mp3")
            subprocess.run([
                "ffmpeg", "-i", video_path, "-q:a", "0", "-map", "a", audio_path, "-y"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Transcribe with Whisper
            result = whisper_model.transcribe(audio_path, word_timestamps=True)
            words = []
            for seg in result["segments"]:
                words.extend(seg["words"])

            # Generate gTTS voice
            story_text = " ".join([w["word"] for w in words])
            tts_path = os.path.join(temp_dir, "voice.mp3")
            gTTS(story_text).save(tts_path)

            # FFmpeg drawtext filter for word-by-word
            def safe(text):
                return re.sub(r"[^a-zA-Z0-9,.?! ]", "", text)

            filters = ""
            for word in words:
                clean = safe(word["word"])
                filters += (
                    f"drawtext=font='Courier':text='{clean}':fontsize=60:"
                    f"fontcolor=white:bordercolor=black:borderw=2:x=(w-text_w)/2:y=(h-text_h)/2:"
                    f"enable='between(t,{word['start']},{word['end']})',"
                )
            filters = filters.rstrip(",")

            # Final output path
            output_path = os.path.join(temp_dir, f"output_{uuid.uuid4().hex}.mp4")

            # Merge everything
            subprocess.run([
                "ffmpeg", "-i", video_path, "-i", tts_path,
                "-vf", filters,
                "-map", "0:v", "-map", "1:a",
                "-c:v", "libx264", "-shortest", output_path, "-y"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Return JSON metadata + optionally serve video URL
            return jsonify({
                "status": "success",
                "message": "Video generated successfully.",
                "prompt": prompt,
                "video_count": len(links),
                "video_path": output_path  # for debug/dev
            })
        # === ADDED FUNCTIONALITY ENDS HERE === #

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "service": "FRAGMENTS AI"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
