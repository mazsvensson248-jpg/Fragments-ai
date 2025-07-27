from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from gtts import gTTS
import uuid
import os

app = Flask(__name__)
CORS(app)

# Skapa en mapp för att spara mp3-filer
AUDIO_FOLDER = "static/audio"
os.makedirs(AUDIO_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return "🚀 Flask Replit API igång!"

@app.route("/api/speech", methods=["POST"])
def speech():
    data = request.get_json()
    text = data.get("text")

    if not text:
        return jsonify({"error": "Ingen text skickad"}), 400

    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(AUDIO_FOLDER, filename)

    tts = gTTS(text=text, lang="sv")
    tts.save(filepath)

    return jsonify({"url": f"/static/audio/{filename}"}), 200

@app.route("/static/audio/<filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
