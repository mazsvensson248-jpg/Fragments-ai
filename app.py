import os
import re
import tempfile
from flask import Flask, request, send_file, jsonify
from pytube import YouTube
from gtts import gTTS
import whisper
import subprocess

app = Flask(__name__)

# Load Whisper model once
model = whisper.load_model("base")

def clean_for_ffmpeg(text):
    # Remove characters that break ffmpeg filter syntax, escape single quotes for drawtext
    text = re.sub(r"[^a-zA-Z0-9,.?! ]", "", text)
    return text.replace("'", r"\'")

def download_youtube_video(url, path):
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension="mp4").order_by("resolution").desc().first()
        if not stream:
            raise Exception("No suitable stream found")
        stream.download(output_path=path, filename="video.mp4")
        return os.path.join(path, "video.mp4")
    except Exception as e:
        raise RuntimeError(f"Failed to download video: {e}")

@app.route('/api/video', methods=['POST'])
def generate_video():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    prompt = data.get("prompt", "").strip()
    links = data.get("links", [])

    if not prompt or not isinstance(links, list) or len(links) == 0 or len(links) > 10:
        return jsonify({"error": "Invalid prompt or links"}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Download first video from YouTube links
            video_path = download_youtube_video(links[0], tmpdir)

            # Generate TTS audio from prompt
            tts_path = os.path.join(tmpdir, "voice.mp3")
            tts = gTTS(text=prompt, lang="en")
            tts.save(tts_path)

            # Transcribe TTS audio with Whisper to get word timings
            result = model.transcribe(tts_path, word_timestamps=True, language="en")
            segments = result.get("segments", [])

            if not segments:
                return jsonify({"error": "Whisper transcription returned no segments"}), 500

            # Create drawtext filter string with system font (e.g., Arial)
            filters = ""
            font_part = "font='Arial':"  # Arial is common, but depends on container

            for segment in segments:
                for word_info in segment.get("words", []):
                    word = clean_for_ffmpeg(word_info["word"])
                    start = word_info["start"]
                    end = word_info["end"]
                    filters += (
                        f"drawtext={font_part}text='{word}':"
                        f"fontsize=48:fontcolor=white:bordercolor=black:borderw=2:"
                        f"x=(w-text_w)/2:y=(h-text_h)/2:"
                        f"enable='between(t,{start},{end})',"
                    )
            filters = filters.rstrip(",")

            # Prepare output video path
            output_path = os.path.join(tmpdir, "final_video.mp4")

            # Run ffmpeg command to combine video and audio, overlay subtitles
            cmd = [
                "ffmpeg",
                "-y",
                "-i", video_path,
                "-i", tts_path,
                "-vf", filters,
                "-map", "0:v",
                "-map", "1:a",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-shortest",
                output_path
            ]

            result_ffmpeg = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result_ffmpeg.returncode != 0 or not os.path.exists(output_path):
                error_msg = result_ffmpeg.stderr.decode(errors='ignore')
                return jsonify({"error": "FFmpeg failed", "details": error_msg}), 500

            return send_file(output_path, mimetype="video/mp4", as_attachment=True, download_name="generated_video.mp4")

        except Exception as e:
            return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
