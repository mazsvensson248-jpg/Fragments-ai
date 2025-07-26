main.py

from flask import Flask, request, jsonify, send_file from flask_cors import CORS from gtts import gTTS from pytube import YouTube import whisper import ffmpeg import os import re

app = Flask(name) CORS(app)

model = whisper.load_model("base")

Helper functions

def clean_for_ffmpeg(text): return re.sub(r"[^a-zA-Z0-9,.?! ]", "", text)

def download_youtube_video(url): yt = YouTube(url) stream = yt.streams.filter(file_extension='mp4').get_highest_resolution() output_path = stream.download() return output_path

def mix_audio(voice_file, music_file): output = "mixed_audio.mp3" os.system(f"ffmpeg -y -i {voice_file} -i {music_file} -filter_complex "[1:a]volume=0.3[a1];[0:a][a1]amix=inputs=2:duration=first" -c:a aac -b:a 192k {output}") return output

def generate_filters(segments): filters = "" for segment in segments: for word_info in segment.get("words", []): word = clean_for_ffmpeg(word_info["word"]) start = word_info["start"] end = word_info["end"] filters += ( f"drawtext=text='{word}':fontcolor=white:fontsize=60:bordercolor=black:borderw=2:x=(w-text_w)/2:y=(h-text_h)/2:enable='between(t,{start},{end})'," ) return filters.rstrip(',')

@app.route("/api/video", methods=["POST"]) def generate_video(): data = request.json prompt = data.get("prompt") links = data.get("links", [])

if not prompt or not links:
    return jsonify({"error": "Missing prompt or video links"}), 400

video_path = download_youtube_video(links[0])

# Generate voice
tts = gTTS(text=prompt, lang="en")
tts.save("voice.mp3")

# Transcribe
result = model.transcribe("voice.mp3", word_timestamps=True, language="en")
segments = result["segments"]
filters = generate_filters(segments)

# Create final video
output_video = "final_video.mp4"
cmd = f"ffmpeg -y -i {video_path} -i voice.mp3 -vf \"{filters}\" -map 0:v -map 1:a -c:v libx264 -c:a aac -shortest {output_video}"
os.system(cmd)

if not os.path.exists(output_video):
    return jsonify({"error": "Failed to create video"}), 500

return send_file(output_video, as_attachment=True)

if name == "main": port = int(os.environ.get("PORT", 10000)) app.run(host="0.0.0.0", port=port)

