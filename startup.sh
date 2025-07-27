#!/bin/bash

# Update & install FFmpeg if needed
apt update && apt install -y ffmpeg

# Run your Python app
python3 app.py
