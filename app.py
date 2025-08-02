from flask import Flask, request, jsonify, send_file
import os
from gtts import gTTS
import whisper
import subprocess
from pytube import YouTube

app = Flask(__name__)

# Health check
@app.route('/')
def index():
    return "✅ App is running fine!"

# Upload endpoint
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    filename = file.filename
    if filename == '':
        return jsonify({"error": "No selected file"}), 400
    file.save(filename)
    return jsonify({"message": f"{filename} uploaded successfully!"}), 200

# Generate TTS audio
@app.route('/generate-voice', methods=['POST'])
def generate_voice():
    data = request.json
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "No text provided!"}), 400

    tts = gTTS(text=text, lang='en')
    output_file = "output_voice.mp3"
    tts.save(output_file)

    return send_file(output_file, as_attachment=True)

# Transcribe audio with Whisper
@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded!"}), 400

    file = request.files['file']
    filename = file.filename
    file.save(filename)

    model = whisper.load_model("base")
    result = model.transcribe(filename)

    os.remove(filename)  # Cleanup

    return jsonify({"transcription": result.get('text', '')})

# Download YouTube video audio
@app.route('/download-audio', methods=['POST'])
def download_audio():
    data = request.json
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "No URL provided!"}), 400

    try:
        yt = YouTube(url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        output_file = "youtube_audio.mp3"
        audio_stream.download(filename=output_file)
        return send_file(output_file, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run FFmpeg command (simple test)
@app.route('/ffmpeg-test', methods=['GET'])
def ffmpeg_test():
    try:
        cmd = ["ffmpeg", "-version"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return jsonify({"ffmpeg_version": result.stdout})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
