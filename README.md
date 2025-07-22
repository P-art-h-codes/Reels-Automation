# Instagram Reel Creation Pipeline 🎬

An automated pipeline for creating engaging Instagram Reels with motivational content, featuring background video generation, Reddit content scraping, and AI-powered text-to-speech narration.

## ✨ Features

- **Automated Background Video Creation**: Generate cinematic background videos from stock footage with professional transitions
- **Content Scraping**: Automatically fetch motivational content from multiple Reddit subreddits
- **AI Text-to-Speech**: Convert text content to natural-sounding voiceovers with multiple voice options
- **Smart Content Filtering**: Automatically filter content based on reading time and engagement metrics
- **Batch Processing**: Create multiple reels in a single pipeline run
- **Customizable Styling**: Multiple text overlay styles and animations
- **Session Management**: Organized output with detailed session tracking

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- FFmpeg (for video processing)
- Espeak-NG (for text-to-speech)
- Windows Build Tools (for Windows users)
- Reddit API credentials

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/instagram-reel-pipeline.git
cd instagram-reel-pipeline
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Create a .env file or set environment variables
export REDDIT_CLIENT_ID="your_reddit_client_id"
export REDDIT_CLIENT_SECRET="your_reddit_client_secret"
```

4. Prepare stock videos:
```bash
mkdir StockVideos
# Add your stock video files (.mp4, .mov, .avi) to this folder
```

### Basic Usage

```bash
# Run the complete pipeline with default settings
python main.py

# Create 10 reels with a specific voice
python main.py --num-reels 10 --voice bf_emma

# Use existing background video
python main.py --existing-bg my_background.mp4 --skip-background

# Custom configuration
python main.py --config my_config.json
```

## 🎯 Pipeline Steps

### 1. Background Video Creation
- Combines multiple stock video clips
- Applies cinematic effects and transitions
- Customizable duration and styling

### 2. Content Scraping
- Scrapes motivational content from Reddit subreddits:
  - r/GetMotivated
  - r/motivation
  - r/wholesomememes
  - r/LifeProTips
  - r/selfimprovement
  - And more...
- Filters by engagement metrics and reading time
- Saves content in JSON and CSV formats

### 3. Reel Generation
- Converts text to speech using AI voices
- Overlays text with customizable styling
- Synchronizes audio with video duration
- Exports ready-to-upload Instagram Reels

## ⚙️ Configuration Options

### Command Line Arguments

```bash
# Background Video Options
--skip-background          # Skip background creation
--existing-bg PATH          # Use existing background video
--bg-duration SECONDS       # Background duration (default: 120)
--effect-type TYPE          # Effect: subtle, cinematic, warm, cool
--transition-type TYPE      # Transition: crossfade, slide, zoom

# Content Options
--skip-scraping            # Skip content scraping
--existing-content PATH    # Use existing content file
--posts-per-sub NUM        # Posts per subreddit (default: 25)
--min-time SECONDS         # Min reading time (default: 30)
--max-time SECONDS         # Max reading time (default: 180)

# Reel Options
--num-reels NUM            # Number of reels to create (default: 5)
--voice VOICE              # TTS voice (see available voices below)
--voice-speed SPEED        # Voice speed (0.5-2.0, default: 1.0)
--text-style STYLE         # Text style: modern, elegant, bold, minimal, vibrant
--text-animation TYPE      # Animation: fade, slide, zoom
--max-duration SECONDS     # Max reel duration (default: 90)
```

### Configuration File

Create a custom configuration file:

```bash
python main.py --create-config my_config.json
```

Example configuration:

```json
{
  "output_folder": "my_reels",
  "background": {
    "duration": 180,
    "effect_type": "warm",
    "transition_type": "crossfade"
  },
  "content": {
    "subreddits": ["GetMotivated", "quotes"],
    "posts_per_sub": 50,
    "min_reading_time": 45,
    "max_reading_time": 120
  },
  "reels": {
    "num_reels": 10,
    "voice": "bf_emma",
    "text_style": "elegant",
    "voice_speed": 0.9
  }
}
```

## 🎤 Available Voices

### American Voices
- **af_heart** - Female, warm and engaging
- **af_bella** - Female, professional
- **af_sarah** - Female, friendly
- **af_nicole** - Female, energetic
- **am_adam** - Male, confident
- **am_michael** - Male, authoritative

### British Voices
- **bf_emma** - Female, elegant
- **bf_isabella** - Female, sophisticated
- **bm_lewis** - Male, refined
- **bm_george** - Male, distinguished

List all available voices:
```bash
python main.py --list-voices
```

## 📁 Output Structure

```
instagram_pipeline_output/
├── session_20241215_143052/
│   ├── backgrounds/
│   │   └── background_20241215_143052.mp4
│   ├── reels/
│   │   ├── reel_001_20241215_143052.mp4
│   │   ├── reel_002_20241215_143052.mp4
│   │   └── ...
│   ├── content_20241215_143052.json
│   ├── content_20241215_143052.csv
│   └── session_summary.json
```

## 🛠️ Advanced Usage

### Skip Steps for Faster Iteration

```bash
# Use existing background and content, only create new reels
python main.py \
  --skip-background --existing-bg backgrounds/my_bg.mp4 \
  --skip-scraping --existing-content content/my_content.json \
  --num-reels 20
```

### Dry Run Configuration Check

```bash
python main.py --dry-run --config my_config.json
```

### Custom Subreddit Mix

```bash
# Focus on specific content types
python main.py \
  --posts-per-sub 100 \
  --min-time 60 \
  --max-time 90 \
  --voice am_adam \
  --text-style bold
```

## 🔧 Troubleshooting

### Common Issues

1. **Reddit API Errors**:
   - Ensure REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET are set
   - Check Reddit API rate limits
   - Verify your Reddit app permissions

2. **FFmpeg Not Found**:
   ```bash
   # Install FFmpeg
   # Windows: Download from https://ffmpeg.org/
   # macOS: brew install ffmpeg
   # Ubuntu: sudo apt install ffmpeg
   ```

3. **No Stock Videos**:
   - Add video files to the `StockVideos/` folder
   - Supported formats: MP4, MOV, AVI
   - Minimum duration: 10 seconds per clip

4. **TTS Voice Errors**:
   - Check internet connection for AI voice generation
   - Try different voice options if one fails
   - Verify voice name spelling

### Debug Mode

Run with verbose output:
```bash
python main.py --config debug_config.json 2>&1 | tee pipeline.log
```

## 📋 Requirements

### System Requirements
- Python 3.8+
- 4GB+ RAM (8GB recommended for batch processing)
- 2GB+ free disk space per session
- Stable internet connection

### API Requirements
- Reddit API credentials (free)
- TTS service access (included)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤖 AI Assistance Disclosure

Parts of this codebase were developed with AI assistance (Claude, ChatGPT, etc.). 
The overall design, architecture, and creative decisions remain the work of the human author(s).

## ⚠️ Disclaimer

- Ensure you have rights to use all stock video content
- Respect Reddit's API terms of service and rate limits
- Review content before publishing to ensure it meets platform guidelines
- This tool is for educational and creative purposes

## 🔗 Related Projects

- [MoviePy](https://github.com/Zulko/moviepy) - Video editing library
- [PRAW](https://github.com/praw-dev/praw) - Reddit API wrapper
- [Kokoro TTS](https://github.com/ai-speech/kokoro-tts) - Text-to-speech engine

## 📞 Support

- Create an [Issue](https://github.com/yourusername/instagram-reel-pipeline/issues) for bug reports
- Start a [Discussion](https://github.com/yourusername/instagram-reel-pipeline/discussions) for feature requests
- Check existing issues before creating new ones

---

**Made with ❤️ for content creators**