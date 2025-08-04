from flask import Flask, render_template, request, jsonify, send_file
import os
import subprocess
import re
import tempfile
import zipfile
from werkzeug.exceptions import BadRequest
from gtts import gTTS
import whisper
from pytube import YouTube
import uuid
import shutil

app = Flask(__name__)

# Create necessary directories
os.makedirs('temp_videos', exist_ok=True)
os.makedirs('output_videos', exist_ok=True)

def clean_for_ffmpeg(text):
    """Clean text for FFmpeg drawtext filter"""
    return re.sub(r"[^a-zA-Z0-9,.?! ]", "", text)

def download_youtube_video(url, output_path):
    """Download YouTube video using pytube"""
    try:
        yt = YouTube(url)
        # Get highest resolution mp4 stream
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        if not stream:
            # Fallback to any mp4 stream
            stream = yt.streams.filter(file_extension='mp4').first()
        
        filename = stream.download(output_path)
        return filename
    except Exception as e:
        raise Exception(f"Failed to download video from {url}: {str(e)}")

def generate_video_with_subtitles(prompt, video_urls, session_id):
    """Generate video with subtitles based on prompt and video URLs"""
    
    session_dir = os.path.join('temp_videos', session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    try:
        # Step 1: Generate voice from prompt
        print("🔊 Generating narrator voice with gTTS...")
        tts = gTTS(text=prompt, lang="en")
        voice_file = os.path.join(session_dir, "voice_output.mp3")
        tts.save(voice_file)
        
        # Step 2: Download YouTube videos
        print("📥 Downloading YouTube videos...")
        downloaded_videos = []
        for i, url in enumerate(video_urls):
            try:
                video_path = download_youtube_video(url, session_dir)
                downloaded_videos.append(video_path)
                print(f"✅ Downloaded video {i+1}/{len(video_urls)}")
            except Exception as e:
                print(f"⚠️ Failed to download {url}: {str(e)}")
                continue
        
        if not downloaded_videos:
            raise Exception("❌ No videos could be downloaded!")
        
        # Step 3: Use first video as main video (you can modify this logic)
        main_video = downloaded_videos[0]
        print(f"🎬 Using main video: {os.path.basename(main_video)}")
        
        # Step 4: Transcribe voice with Whisper
        print("🧠 Transcribing voice with Whisper...")
        model = whisper.load_model("base")
        result = model.transcribe(voice_file, word_timestamps=True, language="en")
        segments = result["segments"]
        
        # Step 5: Create drawtext filter for subtitles
        print("📝 Creating subtitle filters...")
        filters = ""
        
        for segment in segments:
            for word_info in segment.get("words", []):
                word = clean_for_ffmpeg(word_info["word"])
                start = word_info["start"]
                end = word_info["end"]
                filters += (
                    f"drawtext=font='Arial':text='{word}':"
                    f"fontsize=60:fontcolor=white:bordercolor=black:borderw=2:"
                    f"x=(w-text_w)/2:y=(h-text_h)/2:"
                    f"enable='between(t,{start},{end})',"
                )
        
        filters = filters.rstrip(",")
        
        # Step 6: Generate final video with subtitles
        output_file = os.path.join('output_videos', f"{session_id}_final_video.mp4")
        
        print("🎥 Rendering final video with subtitles...")
        cmd = [
            'ffmpeg', '-y',
            '-i', main_video,
            '-i', voice_file,
            '-vf', filters,
            '-map', '0:v', '-map', '1:a',
            '-c:v', 'libx264', '-c:a', 'aac',
            '-shortest', output_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg failed: {result.stderr}")
        
        if not os.path.exists(output_file):
            raise Exception("❌ FFmpeg could not create the video.")
        
        print("✅ Video generation completed!")
        return output_file
        
    except Exception as e:
        raise Exception(f"Video generation failed: {str(e)}")
    
    finally:
        # Clean up temporary files
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)

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
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Start video generation process
        print(f"🚀 Starting video generation for session: {session_id}")
        print(f"📝 Prompt: {prompt}")
        print(f"🎬 Videos: {len(links)} videos")
        
        try:
            output_file = generate_video_with_subtitles(prompt, links, session_id)
            
            return jsonify({
                "status": "success",
                "message": "Video generated successfully!",
                "session_id": session_id,
                "download_url": f"/download/{session_id}"
            })
            
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Video generation failed: {str(e)}"
            }), 500
        
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/download/<session_id>')
def download_video(session_id):
    """Download generated video"""
    try:
        video_file = os.path.join('output_videos', f"{session_id}_final_video.mp4")
        
        if not os.path.exists(video_file):
            return jsonify({"error": "Video not found"}), 404
        
        return send_file(
            video_file,
            as_attachment=True,
            download_name=f"fragments_ai_video_{session_id}.mp4",
            mimetype='video/mp4'
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "service": "FRAGMENTS AI"})

if __name__ == '__main__':
    # Use environment variable for port (required for many deployment platforms)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
