from flask import Flask, request, render_template, jsonify, send_file
from flask_cors import CORS
from gtts import gTTS
import os
import uuid

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/video", methods=["POST"])
def generate_video():
    data = request.get_json()
    prompt = data.get("prompt", "")
    links = data.get("links", [])

    if not prompt or not links:
        return jsonify({"error": "Missing data"}), 400

    dummy_path = "static/dummy.mp4"
    with open(dummy_path, "wb") as f:
        f.write(b"\x00")  # placeholder byte

    return send_file(dummy_path, as_attachment=True, download_name="generated_video.mp4")

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_msg = data.get("message", "")

    if not user_msg:
        return jsonify({"response": "No message sent."}), 400

    return jsonify({"response": f"You said: {user_msg}"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
