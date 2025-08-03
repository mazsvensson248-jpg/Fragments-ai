from flask import Flask, render_template, request, jsonify, send_file
import os
import tempfile
import requests
from werkzeug.exceptions import BadRequest

app = Flask(__name__)

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
        
        # Here you would implement your video generation logic
        # For now, returning a placeholder response
        
        # Example: Create a temporary file as placeholder
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_file.write(b'Placeholder video content')
        temp_file.close()
        
        return jsonify({
            "status": "success",
            "message": "Video generation started",
            "prompt": prompt,
            "video_count": len(links)
        })
        
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "service": "FRAGMENTS AI"})

if __name__ == '__main__':
    # Use environment variable for port (required for many deployment platforms)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
