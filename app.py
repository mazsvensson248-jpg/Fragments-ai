# Required imports
from flask import Flask, request, send_file
import os
import subprocess
import re
from pytube import YouTube
from gtts import gTTS
import whisper
import tempfile
import shutil

app = Flask(__name__)

# Utility functions
def clean_temp_files(temp_paths):
    """Remove all temporary files and directories"""
    for path in temp_paths:
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.exists(path):
                os.remove(path)
        except Exception as e:
            print(f"Error cleaning up {path}: {e}")

def download_youtube_video(url):
    """Download YouTube video at 720p or lower quality"""
    try:
        yt = YouTube(url)
        # Try to get 720p first, fall back to highest available below 720p
        stream = yt.streams.filter(
            progressive=True, 
            file_extension='mp4', 
            res='720p'
        ).first() or yt.streams.filter(
            progressive=True, 
            file_extension='mp4'
        ).order_by('resolution').desc().first()
        
        if not stream:
            raise Exception("No suitable video stream found")
            
        # Download to temp directory
        temp_dir = tempfile.mkdtemp()
        return stream.download(output_path=temp_dir), temp_dir
    except Exception as e:
        raise Exception(f"YouTube download failed: {str(e)}")

def create_subtitle_filter(segments):
    """Create FFmpeg filter for subtitles"""
    def clean_text(text):
        return re.sub(r"[^a-zA-Z0-9,.?! ]", "", text)

    filters = []
    for segment in segments:
        for word_info in segment.get("words", []):
            word = clean_text(word_info["word"])
            start = word_info["start"]
            end = word_info["end"]
            
            filter_text = (
                f"drawtext=font='Arial':text='{word}':"
                f"fontsize=60:fontcolor=white:bordercolor=black:borderw=2:"
                f"x=(w-text_w)/2:y=(h-text_h)/2:"
                f"enable='between(t,{start},{end})'"
            )
            filters.append(filter_text)
    
    return ','.join(filters)

def process_video(story_text, youtube_urls):
    """Main video processing function"""
    temp_paths = []  # Track files to clean up
    
    try:
        # Create working directory
        work_dir = tempfile.mkdtemp()
        temp_paths.append(work_dir)
        
        # 1. Generate voice narration
        print("🎤 Generating voice narration...")
        voice_path = os.path.join(work_dir, "narration.mp3")
        tts = gTTS(text=story_text, lang="en")
        tts.save(voice_path)
        temp_paths.append(voice_path)
        
        # 2. Generate transcript with timestamps
        print("📝 Creating transcript...")
        model = whisper.load_model("base")
        result = model.transcribe(voice_path, word_timestamps=True)
        
        # 3. Download YouTube videos
        print("📥 Downloading videos...")
        video_segments = []
        for url in youtube_urls:
            video_path, temp_dir = download_youtube_video(url)
            video_segments.append(video_path)
            temp_paths.extend([video_path, temp_dir])
        
        # 4. Combine videos if multiple
        if len(video_segments) > 1:
            print("🔄 Combining videos...")
            concat_list = os.path.join(work_dir, "concat.txt")
            with open(concat_list, 'w') as f:
                for video in video_segments:
                    f.write(f"file '{video}'\n")
            
            combined_video = os.path.join(work_dir, "combined.mp4")
            subprocess.run([
                'ffmpeg', '-f', 'concat', '-safe', '0',
                '-i', concat_list, '-c', 'copy', combined_video
            ], check=True)
            
            input_video = combined_video
            temp_paths.extend([concat_list, combined_video])
        else:
            input_video = video_segments[0]
        
        # 5. Create final video with subtitles and audio
        print("🎬 Creating final video...")
        output_path = os.path.join(work_dir, "final_output.mp4")
        subtitle_filter = create_subtitle_filter(result["segments"])
        
        subprocess.run([
            'ffmpeg', '-y',
            '-i', input_video,
            '-i', voice_path,
            '-vf', subtitle_filter,
            '-map', '0:v',
            '-map', '1:a',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-shortest',
            output_path
        ], check=True)
        
        return output_path, temp_paths
    
    except Exception as e:
        clean_temp_files(temp_paths)
        raise Exception(f"Video processing failed: {str(e)}")

# API Endpoints
@app.route('/api/video', methods=['POST'])
def generate_video():
    try:
        # Get request data
        data = request.get_json()
        story = data.get('prompt')
        youtube_links = data.get('links', [])
        
        # Validate input
        if not story or not youtube_links:
            return {"error": "Missing prompt or video links"}, 400
        
        if len(youtube_links) > 10:
            return {"error": "Maximum 10 videos allowed"}, 400
        
        # Process video
        output_file, temp_paths = process_video(story, youtube_links)
        
        # Send response
        try:
            return send_file(
                output_file,
                mimetype='video/mp4',
                as_attachment=True,
                download_name='generated_video.mp4'
            )
        finally:
            clean_temp_files(temp_paths)
            
    except Exception as e:
        return {"error": str(e)}, 500

# Server startup
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
