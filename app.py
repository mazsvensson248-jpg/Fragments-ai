from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Create static directory if not exists
os.makedirs("static", exist_ok=True)

@app.route("/")
def home():
    return "<h1>FRAGMENTS AI</h1><p>Welcome to the AI backend.</p>"

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "")
    if not message:
        return jsonify({"response": "No message received."}), 400

    # Dummy AI response
    return jsonify({"response": f"You said: {message}"})

@app.route("/api/video", methods=["POST"])
def generate_video():
    data = request.get_json()
    prompt = data.get("prompt", "")
    links = data.get("links", [])

    if not prompt or not links:
        return jsonify({"error": "Missing prompt or links."}), 400

    # Create a dummy video file
    dummy_path = "static/dummy.mp4"
    with open(dummy_path, "wb") as f:
        f.write(b"\x00")

    return send_file(dummy_path, as_attachment=True, download_name="generated_video.mp4")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
