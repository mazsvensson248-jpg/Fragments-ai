from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import logging
import os
import datetime

# === Initialize App ===
app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

# === Logging Setup ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("FRAGMENTS-API")

# === Routes ===

@app.route("/")
def serve_index():
    logger.info("Serving frontend HTML...")
    return send_from_directory("static", "index.html")

@app.route("/generate", methods=["POST"])
def generate_video():
    data = request.get_json()

    prompt = data.get("prompt")
    youtube_links = data.get("youtube_links")

    logger.info("Generate request received.")
    logger.info(f"Prompt: {prompt}")
    logger.info(f"Videos: {youtube_links}")

    if not prompt or not youtube_links:
        logger.warning("Missing prompt or YouTube links.")
        return jsonify({"error": "Missing prompt or YouTube links"}), 400

    # === Placeholder logic ===
    try:
        # You can replace this with actual generation logic
        logger.info("Pretending to generate videos...")
        return jsonify({"message": "✅ Video generation started!"})
    except Exception as e:
        logger.error(f"Generation failed: {str(e)}")
        return jsonify({"error": "Video generation failed."}), 500

@app.route("/chat", methods=["POST"])
def ai_chat():
    data = request.get_json()
    user_input = data.get("message")

    logger.info(f"Chat message received: {user_input}")

    if not user_input:
        return jsonify({"error": "Message is required"}), 400

    # TODO: Integrate with real AI
    response = f"🤖 Echo: {user_input}"
    logger.info(f"AI Responds: {response}")
    return jsonify({"response": response})

@app.errorhandler(404)
def not_found(e):
    logger.warning("404 - Not Found")
    return jsonify({"error": "Route not found"}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"500 - Internal Server Error: {e}")
    return jsonify({"error": "Internal Server Error"}), 500

# === Run App ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🔥 FRAGMENTS API starting on port {port}")
    app.run(host="0.0.0.0", port=port)
