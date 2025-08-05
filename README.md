# 🚂 FRAGMENTS AI - Railway.com Exclusive

**⚠️ This application is exclusively designed for Railway.com deployment and will NOT work on other platforms.**

## 🎯 Railway.com Features

- **100% Railway Optimized**: Built specifically for Railway's infrastructure
- **Zero Error Deployment**: Tested and optimized for Railway.com
- **Fast Processing**: 2-4 minute video generation on Railway
- **Ephemeral Storage**: Uses Railway's temporary file system
- **Auto-scaling**: Railway handles traffic spikes automatically

## 🚀 Railway Deployment Steps

### 1. Connect GitHub to Railway

1. Go to [Railway.app](https://railway.app)
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Connect your repository

### 2. Railway Configuration

Railway will automatically detect the configuration from:
- `nixpacks.toml` - Build configuration
- `Procfile` - Process configuration
- `requirements.txt` - Python dependencies

### 3. Environment Variables (Optional)

Railway sets these automatically:
- `RAILWAY_ENVIRONMENT=production`
- `PORT` (automatically assigned)
- `PYTHONPATH` (automatically configured)

### 4. Deploy

Click "Deploy" - Railway handles everything automatically!

## 🔧 Railway-Specific Optimizations

### Performance Optimizations
```python
# Railway-optimized settings
- Tiny Whisper model for speed
- 480p video quality for Railway bandwidth
- 60-second video limit
- Single worker process
- Ephemeral storage (/tmp)
```

### Memory Management
```python
# Railway memory optimizations
- Limited prompt length (300 chars)
- CPU-only PyTorch
- Automatic cleanup
- Minimal dependencies
```

### Error Handling
```python
# Railway-specific error handling
- Connection retry logic
- Graceful degradation
- Comprehensive logging
- Health check endpoints
```

## 📁 Railway File Structure

```
railway-fragments-ai/
├── main.py              # Railway main application
├── requirements.txt     # Railway-optimized dependencies
├── Dockerfile          # Railway container config
├── Procfile            # Railway process config
├── nixpacks.toml       # Railway build config
├── .dockerignore       # Railway Docker ignore
├── .gitignore          # Railway Git ignore
├── templates/
│   └── index.html      # Web interface
└── README.md           # This file
```

## 🛠️ Railway Technical Details

### System Requirements
- **Platform**: Railway.com only
- **Python**: 3.11 (Railway managed)
- **FFmpeg**: Automatically installed
- **Storage**: Railway ephemeral (/tmp)
- **Memory**: Railway auto-scaling

### Railway Limits
| Feature | Railway Limit |
|---------|---------------|
| Video Length | 60 seconds max |
| File Size | 50MB max |
| Processing Time | 5 minutes max |
| Concurrent Users | Railway auto-scaling |
| Storage | Ephemeral only |

### Railway Dependencies
```txt
Flask==2.3.3          # Railway-tested version
openai-whisper==20231117  # Railway-compatible
pytube==15.0.0        # Railway-optimized
torch==2.1.0+cpu      # Railway CPU-only
```

## 🚨 Railway-Only Features

### Exclusive Railway Functions
- `railway_only_check()` - Ensures Railway environment
- `download_youtube_railway()` - Railway-optimized downloads
- `generate_video_railway()` - Railway-specific processing
- `process_async_railway()` - Railway threading

### Railway Error Prevention
- Automatic Railway environment detection
- Railway-specific timeout handling
- Railway memory optimization
- Railway storage management

## 📊 Railway Monitoring

### Health Checks
- `/health` - Railway health endpoint
- Automatic Railway
