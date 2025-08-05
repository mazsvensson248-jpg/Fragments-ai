from flask import Flask, render_template, request, jsonify, send_file
import os
import subprocess
import re
import threading
import tempfile
from werkzeug.exceptions import BadRequest
from gtts import gTTS
import whisper
from pytube import YouTube
import uuid
import shutil
import logging

# Railway-specific logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Railway optimized configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB for Railway
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Railway ephemeral storage paths
TEMP_DIR = "/tmp/fragments_temp"
OUTPUT_DIR = "/tmp/fragments_output"
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# In-memory status storage for Railway
processing_status = {}

def railway_only_check():
    """Ensure this only works on Railway.com"""
    if not os.environ.get('RAILWAY_ENVIRONMENT'):
        raise Exception("❌ This app is exclusively designed for Railway.com deployment")
    return True

def clean_text_railway(text):
    """Railway-safe text cleaning"""
    if not text:
        return ""
    text = str(text).strip()[:100]  # Limit for Railway performance
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    return text.replace("'", "").replace('"', '').replace('\\', '')

def download_youtube_railway(url, output_path, session_id):
    """Railway-optimized YouTube download"""
    try:
        processing_status[session_id]['step'] = "Downloading video..."
        logger.info(f"Railway download starting: {session_id}")
        
        yt = YouTube(url, use_oauth=False, allow_oauth_cache=False)
        
        # Railway prefers progressive streams
        stream = yt.streams.filter(progressive=True, file_extension='mp4', resolution='480p').first()
        if not stream:
            stream = yt.streams.filter(progressive=True, file_extension='mp4').first()
        if not stream:
            stream = yt.streams.filter(file_extension='mp4').first()
        
        if not stream:
            raise Exception("No suitable video stream found")
        
        filename = f"railway_bg_{session_id}.mp4"
        filepath = os.path.join(output_path, filename)
        
        stream.download(output_path, filename=filename)
        logger.info(f"✅ Railway download complete: {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Railway download error: {e}")
        raise Exception(f"Download failed: {str(e)}")

def generate_video_railway(prompt, video_urls, session_id):
    """Railway-optimized video generation"""
    session_dir = os.path.join(TEMP_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    try:
        # Railway check
        railway_only_check()
        
        processing_status[session_id] = {'step': 'Railway processing...', 'progress': 0, 'status': 'processing'}
        
        # Step 1: Generate speech (Railway optimized)
        processing_status[session_id]['step'] = "Generating speech..."
        processing_status[session_id]['progress'] = 20
        
        prompt_clean = prompt[:300]  # Railway length limit
        tts = gTTS(text=prompt_clean, lang="en", slow=False)
        voice_file = os.path.join(session_dir, "voice.mp3")
        tts.save(voice_file)
        
        # Convert to WAV for Railway
        wav_file = os.path.join(session_dir, "voice.wav")
        subprocess.run([
            'ffmpeg', '-y', '-i', voice_file,
            '-acodec', 'pcm_s16le', '-ar', '16000',
            wav_file
        ], check=True, capture_output=True, timeout=120)
        
        processing_status[session_id]['progress'] = 40
        
        # Step 2: Download video
        processing_status[session_id]['step'] = "Downloading background..."
        background_video = download_youtube_railway(video_urls[0], session_dir, session_id)
        processing_status[session_id]['progress'] = 60
        
        # Step 3: Transcribe with Railway-optimized Whisper
        processing_status[session_id]['step'] = "Creating subtitles..."
        model = whisper.load_model("tiny")  # Fastest for Railway
        result = model.transcribe(wav_file, word_timestamps=True, language="en")
        processing_status[session_id]['progress'] = 75
        
        # Step 4: Create subtitle filters
        processing_status[session_id]['step'] = "Rendering video..."
        drawtext_filters = []
        
        for segment in result["segments"]:
            for word_info in segment.get("words", []):
                word = clean_text_railway(word_info["word"])
                if word:
                    start_time = word_info["start"]
                    end_time = word_info["end"]
                    
                    filter_text = (
                        f"drawtext=text='{word}'"
                        f":fontsize=40"
                        f":fontcolor=white"
                        f":bordercolor=black"
                        f":borderw=2"
                        f":x=(w-text_w)/2"
                        f":y=h*0.85"
                        f":enable='between(t,{start_time},{end_time})'"
                    )
                    drawtext_filters.append(filter_text)
        
        # Step 5: Railway FFmpeg processing
        output_file = os.path.join(OUTPUT_DIR, f"railway_{session_id}.mp4")
        
        if drawtext_filters:
            video_filter = ",".join(drawtext_filters[:50])  # Limit for Railway
        else:
            video_filter = "null"
        
        cmd = [
            'ffmpeg', '-y',
            '-i', background_video,
            '-i', wav_file,
            '-filter_complex', f'[0:v]{video_filter}[v]',
            '-map', '[v]', '-map', '1:a',
            '-c:v', 'libx264', '-preset', 'fast',
            '-crf', '28',  # Railway optimized quality
            '-c:a', 'aac', '-b:a', '96k',
            '-t', '60',  # 60 second limit for Railway
            '-movflags', '+faststart',
            output_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg failed: {result.stderr}")
        
        if not os.path.exists(output_file) or os.path.getsize(output_file) < 1000:
            raise Exception("Video generation failed")
        
        processing_status[session_id]['step'] = "Complete!"
        processing_status[session_id]['progress'] = 100
        processing_status[session_id]['status'] = 'completed'
        processing_status[session_id]['output_file'] = output_file
        
        logger.info(f"✅ Railway video generation complete: {session_id}")
        return output_file
        
    except Exception as e:
        processing_status[session_id]['status'] = 'failed'
        processing_status[session_id]['error'] = str(e)
        logger.error(f"Railway generation error: {e}")
        raise
    
    finally:
        # Railway cleanup
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir, ignore_errors=True)

def process_async_railway(prompt, video_urls, session_id):
    """Railway async processing"""
    try:
        generate_video_railway(prompt, video_urls, session_id)
    except Exception as e:
        logger.error(f"Railway async error: {e}")

# Railway Flask routes
@app.route('/')
def index():
    railway_only_check()
    return render_template('index.html')

@app.route('/api/video', methods=['POST'])
def generate_video():
    try:
        railway_only_check()
        
        data = request.get_json()
        if not data:
            raise BadRequest("No data provided")
        
        prompt = data.get('prompt', '').strip()
        links = data.get('links', [])
        
        if not prompt:
            raise BadRequest("Prompt required")
        if not links or len(links) > 5:  # Railway limit
            raise BadRequest("Please provide 1-5 video links")
        
        session_id = str(uuid.uuid4())
        
        # Start Railway processing
        thread = threading.Thread(
            target=process_async_railway,
            args=(prompt, links, session_id)
        )
        thread.start()
        
        return jsonify({
            "status": "started",
            "message": "Railway video generation started!",
            "session_id": session_id
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/status/<session_id>')
def get_status(session_id):
    railway_only_check()
    if session_id not in processing_status:
        return jsonify({"error": "Session not found"}), 404
    return jsonify(processing_status[session_id])

@app.route('/download/<session_id>')
def download_video(session_id):
    try:
        railway_only_check()
        
        if session_id not in processing_status:
            return jsonify({"error": "Session not found"}), 404
        
        status = processing_status[session_id]
        if status.get('status') != 'completed':
            return jsonify({"error": "Video not ready"}), 400
        
        output_file = status.get('output_file')
        if not output_file or not os.path.exists(output_file):
            return jsonify({"error": "File not found"}), 404
        
        return send_file(
            output_file,
            as_attachment=True,
            download_name=f"railway_fragments_video.mp4"
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health():
    railway_only_check()
    return jsonify({"status": "Railway ready", "service": "FRAGMENTS AI"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
