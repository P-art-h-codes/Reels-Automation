#!/usr/bin/env python3
"""
Instagram Reel Creator with Kokoro TTS - Fixed PIL Compatibility
A clean, modern implementation for creating Instagram Reels with AI-generated voiceovers.
"""

import os
import json
import csv
import random
import tempfile
import shutil
from datetime import datetime
import argparse
from pathlib import Path
import textwrap
import time
import subprocess
import sys

# Third-party imports
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import *
import torch

# Fix PIL compatibility issue
try:
    # For newer Pillow versions (>=10.0.0)
    # Apologies for monkey patching (i dont have expertise in moviepy)
    from PIL import Image
    if not hasattr(Image, 'ANTIALIAS'):
        Image.ANTIALIAS = Image.LANCZOS
        Image.NEAREST = getattr(Image.Resampling, 'NEAREST', Image.NEAREST)
        Image.BILINEAR = getattr(Image.Resampling, 'BILINEAR', Image.BILINEAR)
        Image.BICUBIC = getattr(Image.Resampling, 'BICUBIC', Image.BICUBIC)
        Image.LANCZOS = getattr(Image.Resampling, 'LANCZOS', Image.LANCZOS)
except (AttributeError, ImportError):
    # For older Pillow versions, these should already exist
    pass

from kokoro.__main__ import generate_and_save_audio

class ReelTextRenderer:
    """Handle text styling and rendering for reels"""
    
    def __init__(self, width=1080, height=1920):
        self.width = width
        self.height = height
        
        # Text style presets
        self.styles = {
            'modern': {
                'font_size': 60,
                'color': (255, 255, 255),      # White
                'stroke_color': (0, 0, 0),     # Black
                'stroke_width': 3,
                'bg_opacity': 0.7
            },
            'elegant': {
                'font_size': 55,
                'color': (255, 255, 255),      # White  
                'stroke_color': (25, 25, 112),  # Navy
                'stroke_width': 2,
                'bg_opacity': 0.6
            },
            'bold': {
                'font_size': 70,
                'color': (255, 255, 0),        # Yellow
                'stroke_color': (0, 0, 0),     # Black
                'stroke_width': 4,
                'bg_opacity': 0.8
            },
            'minimal': {
                'font_size': 50,
                'color': (255, 255, 255),      # White
                'stroke_color': (128, 128, 128), # Gray
                'stroke_width': 1,
                'bg_opacity': 0.5
            },
            'vibrant': {
                'font_size': 65,
                'color': (255, 215, 0),        # Gold
                'stroke_color': (139, 69, 19),  # Brown
                'stroke_width': 3,
                'bg_opacity': 0.7
            }
        }
    
    def get_font(self, size):
        """Get the best available font"""
        font_paths = [
            # Windows fonts
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            # macOS fonts  
            "/System/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
            # Linux fonts
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        ]
        
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, size)
            except Exception as e:
                print(f"⚠️ Could not load font {font_path}: {e}")
                continue
        
        # Fallback to default font
        try:
            return ImageFont.load_default()
        except Exception as e:
            print(f"⚠️ Could not load default font: {e}")
            return None
    
    def create_text_image(self, text, style_name='modern'):
        """Create a text image with the specified style"""
        style = self.styles.get(style_name, self.styles['modern'])
        
        # Create image with transparent background
        img_height = 300
        img = Image.new('RGBA', (self.width, img_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Get font
        font = self.get_font(style['font_size'])
        if not font:
            return self._create_fallback_image(text, style, img_height)
        
        # Wrap text to fit width
        wrapped_text = textwrap.fill(text, width=20)
        lines = wrapped_text.split('\n')
        
        # Calculate text positioning
        line_spacing = style['font_size'] + 10
        total_height = len(lines) * line_spacing
        y_start = (img_height - total_height) // 2
        
        # Draw text with stroke effect
        for i, line in enumerate(lines):
            if not line.strip():
                continue
                
            # Get text dimensions
            try:
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
            except AttributeError:
                # Fallback for older Pillow versions
                text_width, text_height = draw.textsize(line, font=font)
            
            x = (self.width - text_width) // 2
            y = y_start + i * line_spacing
            
            # Draw stroke (outline)
            stroke_width = style['stroke_width']
            for dx in range(-stroke_width, stroke_width + 1):
                for dy in range(-stroke_width, stroke_width + 1):
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), line, 
                                font=font, fill=style['stroke_color'])
            
            # Draw main text
            draw.text((x, y), line, font=font, fill=style['color'])
        
        return img
    
    def _create_fallback_image(self, text, style, img_height):
        """Create simple text fallback when fonts aren't available"""
        img = Image.new('RGBA', (self.width, img_height), (0, 0, 0, 180))
        draw = ImageDraw.Draw(img)
        
        # Simple text rendering without custom fonts
        lines = textwrap.fill(text, width=30).split('\n')
        y_pos = img_height // 4
        
        for line in lines[:4]:  # Limit to 4 lines
            if line.strip():
                draw.text((50, y_pos), line[:60], fill=(255, 255, 255))
                y_pos += 40
        
        return img
    
    def create_text_clips(self, text, duration, style='modern', animation='fade'):
        """Create animated text clips for the reel"""
        # Split text into chunks for better readability
        words = text.split()
        chunk_size = 8  # Words per chunk
        chunks = [' '.join(words[i:i + chunk_size]) 
                 for i in range(0, len(words), chunk_size)]
        
        if not chunks:
            return []
        
        text_clips = []
        chunk_duration = duration / len(chunks)
        
        for i, chunk in enumerate(chunks):
            start_time = i * chunk_duration
            
            try:
                # Create text image
                text_img = self.create_text_image(chunk, style)
                img_array = np.array(text_img)
                
                # Create video clip
                img_clip = ImageClip(img_array, duration=chunk_duration, transparent=True)
                img_clip = img_clip.set_position('center').set_start(start_time)
                
                # Apply animation
                img_clip = self._apply_animation(img_clip, animation, i, len(chunks))
                text_clips.append(img_clip)
                
            except Exception as e:
                print(f"⚠️ Error creating text clip {i+1}: {e}")
                # Create a simple colored rectangle as fallback
                fallback_clip = ColorClip(
                    size=(800, 100), 
                    color=(255, 255, 255),
                    duration=chunk_duration
                ).set_position('center').set_start(start_time)
                text_clips.append(fallback_clip)
        
        return text_clips
    
    def _apply_animation(self, clip, animation, index, total_clips):
        """Apply animation effects to text clips"""
        try:
            if animation == 'fade':
                if index == 0:
                    clip = clip.fadein(0.5)
                if index == total_clips - 1:
                    clip = clip.fadeout(0.5)
                else:
                    clip = clip.fadeout(0.3)
                    
            elif animation == 'slide':
                # Slide up from bottom
                def slide_position(t):
                    if t < 0.5:
                        progress = t / 0.5
                        y_offset = (1 - progress) * 200
                        return ('center', f'center+{y_offset}')
                    return 'center'
                clip = clip.set_position(slide_position)
                
            elif animation == 'zoom':
                # Subtle zoom effect
                clip = clip.resize(lambda t: min(1 + t * 0.05, 1.05))
        
        except Exception as e:
            print(f"⚠️ Animation error: {e}")
            # Return clip without animation as fallback
        
        return clip

class InstagramReelCreator:
    """Main class for creating Instagram Reels"""
    
    def __init__(self, output_folder="instagram_reels"):
        self.output_folder = Path(output_folder)
        self.temp_folder = Path(tempfile.mkdtemp(prefix="reel_temp_"))
        
        # Create output folder
        self.output_folder.mkdir(exist_ok=True)
        
        # Initialize components
        self.text_renderer = ReelTextRenderer()
        
        print(f"📁 Output folder: {self.output_folder}")
        print(f"🔧 Temp folder: {self.temp_folder}")
    
    def load_content(self, file_path):
        """Load content from JSON or CSV file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Content file not found: {file_path}")
        
        content = []
        
        if file_path.suffix.lower() == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
        elif file_path.suffix.lower() == '.csv':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = list(csv.DictReader(f))
        else:
            raise ValueError("Content file must be JSON or CSV format")
        
        print(f"📚 Loaded {len(content)} content items")
        return content
    
    def list_voices(self):
        """List all available Kokoro voices"""
        voices = [
            "af_heart",    # American 
            "af_bella",    # American Female - Bella
            "af_sarah",    # American Female - Sarah  
            "af_nicole",   # American Female - Nicole
            "am_adam",     # American Male - Adam
            "am_michael",  # American Male - Michael
            "bf_emma",     # British Female - Emma
            "bf_isabella", # British Female - Isabella
            "bm_lewis",    # British Male - Lewis
            "bm_george"    # British Male - George
        ]

        print("Available Kokoro voices:")
        for voice in voices:
            print(f"  - {voice}")

    def create_single_reel(self, background_video, content_item, lang='a',
                          voice='af_heart', style='modern', animation='fade', 
                          voice_speed=1.0, max_duration=90):
        """Create a single Instagram Reel"""
        
        try:
            # Load and prepare background video
            print(f"🎬 Processing background video...")
            bg_video = VideoFileClip(str(background_video))
            
            # Extract text content
            title = content_item.get('title', '')
            content_text = content_item.get('content', '') or content_item.get('text', '')
            
            # Combine and clean text
            full_text = f"{title}. {content_text}".strip()
            if not full_text or full_text == '.':
                raise ValueError("No valid text content found")
            
            # Limit text length
            words = full_text.split()
            if len(words) > 200:  # Limit to ~200 words
                full_text = ' '.join(words[:200]) + '...'
            
            print(f"📝 Text: {len(words)} words")
            
            # Generate voice-over
            audio_file = self.temp_folder / "temp_audio.wav"
            try:
                generate_and_save_audio(
                    output_file=audio_file,
                    text=full_text,
                    kokoro_language=lang,
                    voice=voice,
                    speed=voice_speed
                )
            except Exception as e:
                print(f"⚠️ Audio generation failed: {e}")
                audio_file = None
            
            # Load audio and determine duration
            if audio_file and audio_file.exists():
                try:
                    audio_clip = AudioFileClip(str(audio_file))
                    target_duration = min(audio_clip.duration, max_duration)
                except Exception as e:
                    print(f"⚠️ Audio loading failed: {e}")
                    audio_clip = None
                    target_duration = min(len(words) / 2.5, max_duration)
            else:
                # Estimate duration if audio generation failed
                target_duration = min(len(words) / 2.5, max_duration)
                audio_clip = None
            
            print(f"⏱️  Target duration: {target_duration:.1f}s")
            
            # Prepare background video
            if bg_video.duration > target_duration:
                # Use random segment
                start_time = random.uniform(0, max(0, bg_video.duration - target_duration))
                bg_video = bg_video.subclip(start_time, start_time + target_duration)
            else:
                # Loop if necessary
                bg_video = bg_video.loop(duration=target_duration)
            
            # Resize background to Instagram format (9:16) with error handling
            try:
                bg_video = bg_video.resize((1080, 1920))
            except Exception as e:
                print(f"⚠️ Video resize error: {e}")
                # Try alternative resize approach
                bg_video = bg_video.resize(height=1920).resize(width=1080)
            
            # Create text overlays
            print("✏️  Creating text overlays...")
            text_clips = self.text_renderer.create_text_clips(
                full_text, target_duration, style=style, animation=animation
            )
            
            # Add subtitle backgrounds
            enhanced_clips = []
            for text_clip in text_clips:
                try:
                    # Semi-transparent background
                    bg_clip = ColorClip(
                        size=(1080, 250), 
                        color=(0, 0, 0),
                        duration=text_clip.duration
                    ).set_opacity(0.6).set_position('center').set_start(text_clip.start)
                    
                    enhanced_clips.extend([bg_clip, text_clip])
                except Exception as e:
                    print(f"⚠️ Error creating background for text clip: {e}")
                    enhanced_clips.append(text_clip)
            
            # Compose final video
            all_clips = [bg_video] + enhanced_clips
            final_video = CompositeVideoClip(all_clips, size=(1080, 1920))
            
            # Add audio if available
            if audio_clip:
                try:
                    final_video = final_video.set_audio(audio_clip)
                except Exception as e:
                    print(f"⚠️ Audio attachment failed: {e}")
            
            final_video = final_video.set_duration(target_duration)
            
            return final_video
            
        except Exception as e:
            print(f"❌ Error creating reel: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def create_batch_reels(self, background_video, content_file, num_reels=1, **kwargs):
        """Create multiple reels from content file"""
        
        # Load content
        content_data = self.load_content(content_file)
        
        if len(content_data) < num_reels:
            print(f"⚠️  Only {len(content_data)} items available, creating {len(content_data)} reels")
            num_reels = len(content_data)
        
        # Select random content
        selected_content = random.sample(content_data, num_reels)
        
        created_reels = []
        
        for i, content_item in enumerate(selected_content, 1):
            print(f"\n--- Creating Reel {i}/{num_reels} ---")
            
            title = content_item.get('title', 'Untitled')[:50]
            print(f"📄 Title: {title}...")
            
            # Create the reel
            reel_video = self.create_single_reel(
                background_video, content_item, **kwargs
            )
            
            if reel_video:
                # Generate filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_title = "".join(c for c in title if c.isalnum() or c in ' -_')
                safe_title = safe_title.replace(' ', '_')[:20]
                
                output_file = self.output_folder / f"reel_{i:02d}_{safe_title}_{timestamp}.mp4"
                
                # Export video with error handling
                print(f"💾 Exporting: {output_file.name}")
                try:
                    reel_video.write_videofile(
                        str(output_file),
                        fps=30,
                        codec='libx264',
                        audio_codec='aac',
                        preset='medium',
                        ffmpeg_params=['-crf', '23', '-pix_fmt', 'yuv420p'],
                        verbose=False,
                        logger=None
                    )
                    
                    created_reels.append({
                        'file': output_file,
                        'title': title,
                        'duration': reel_video.duration
                    })
                    
                    print(f"✅ Reel {i} completed ({reel_video.duration:.1f}s)")
                    
                except Exception as e:
                    print(f"❌ Export failed for reel {i}: {e}")
                
                # Cleanup
                try:
                    reel_video.close()
                except:
                    pass
                
            else:
                print(f"❌ Failed to create reel {i}")
        
        return created_reels
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            if self.temp_folder.exists():
                shutil.rmtree(self.temp_folder)
                print("🧹 Cleaned up temporary files")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
    
    def __del__(self):
        """Ensure cleanup on object destruction"""
        self.cleanup()

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Create Instagram Reels with Kokoro TTS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python reel_creator.py -b video.mp4 -c content.json
  python reel_creator.py -b video.mp4 -c content.csv -n 5 --voice af_heart
  python reel_creator.py --list-voices
        """
    )
    
    parser.add_argument("--background", "-b", 
                       help="Background video file path")
    parser.add_argument("--content", "-c",
                       help="Content file (JSON or CSV)")
    parser.add_argument("--num-reels", "-n", type=int, default=1,
                       help="Number of reels to create (default: 1)")
    parser.add_argument("--voice", default="af_heart",
                       help="Kokoro voice to use (default: af_heart)")
    parser.add_argument("--voice-speed", type=float, default=1.0,
                       help="Voice speed 0.5-2.0 (default: 1.0)")
    parser.add_argument("--style", choices=['modern', 'elegant', 'bold', 'minimal', 'vibrant'],
                       default='modern', help="Text style (default: modern)")
    parser.add_argument("--animation", choices=['fade', 'slide', 'zoom'],
                       default='fade', help="Text animation (default: fade)")
    parser.add_argument("--max-duration", type=int, default=90,
                       help="Maximum reel duration in seconds (default: 90)")
    parser.add_argument("--list-voices", action='store_true',
                       help="List available voices and exit")
    parser.add_argument("--output", "-o", default="instagram_reels",
                       help="Output folder (default: instagram_reels)")
    
    args = parser.parse_args()
    
    try:
        # Initialize creator
        creator = InstagramReelCreator(args.output)
        
        # List voices if requested
        if args.list_voices:
            creator.list_voices()
            return 0
        
        # Validate required arguments
        if not args.background or not args.content:
            print("❌ Error: --background and --content are required")
            print("Use --help for more information")
            return 1
        
        if not Path(args.background).exists():
            print(f"❌ Error: Background video not found: {args.background}")
            return 1
        
        if not Path(args.content).exists():
            print(f"❌ Error: Content file not found: {args.content}")
            return 1
        
        # Show configuration
        print("🎬 Instagram Reel Creator")
        print("=" * 50)
        print(f"Background Video: {args.background}")
        print(f"Content File: {args.content}")
        print(f"Number of Reels: {args.num_reels}")
        print(f"Voice: {args.voice}")
        print(f"Voice Speed: {args.voice_speed}x")
        print(f"Text Style: {args.style}")
        print(f"Animation: {args.animation}")
        print(f"Max Duration: {args.max_duration}s")
        print(f"Output Folder: {args.output}")
        print("=" * 50)
        
        # Create reels
        start_time = time.time()
        
        created_reels = creator.create_batch_reels(
            background_video=args.background,
            content_file=args.content,
            num_reels=args.num_reels,
            voice=args.voice,
            voice_speed=args.voice_speed,
            style=args.style,
            animation=args.animation,
            max_duration=args.max_duration
        )
        
        # Summary
        elapsed_time = time.time() - start_time
        total_duration = sum(reel['duration'] for reel in created_reels)
        
        print("\n" + "=" * 50)
        print("🎉 SUMMARY")
        print("=" * 50)
        print(f"✅ Successfully created {len(created_reels)} reels")
        print(f"⏱️  Processing time: {elapsed_time:.1f}s")
        print(f"🎬 Total video duration: {total_duration:.1f}s")
        print(f"📁 Output folder: {creator.output_folder}")
        
        if created_reels:
            print("\nCreated Files:")
            for reel in created_reels:
                print(f"  📹 {reel['file'].name} ({reel['duration']:.1f}s)")
        
        # Cleanup
        creator.cleanup()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())