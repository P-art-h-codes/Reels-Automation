import os
import json
import csv
import random
from datetime import datetime
import argparse
from moviepy.editor import *
from moviepy.video.fx import resize
import numpy as np
import textwrap
import pyttsx3
import threading
import queue
import time
from PIL import Image, ImageDraw, ImageFont
import io

class InstagramReelCreator:
    def __init__(self, output_folder="final_reels"):
        self.output_folder = output_folder
        self.temp_folder = "temp_audio"
        self.target_width = 1080
        self.target_height = 1920
        
        # Create folders if they don't exist
        os.makedirs(output_folder, exist_ok=True)
        os.makedirs(self.temp_folder, exist_ok=True)
        
        # Text styling options
        self.text_styles = {
            'modern': {
                'fontsize': 60,
                'color': (255, 255, 255),  # White
                'stroke_color': (0, 0, 0),  # Black
                'stroke_width': 3,
                'font_name': 'arial.ttf'
            },
            'elegant': {
                'fontsize': 55,
                'color': (255, 255, 255),  # White
                'stroke_color': (25, 25, 112),  # Navy
                'stroke_width': 2,
                'font_name': 'georgia.ttf'
            },
            'bold': {
                'fontsize': 70,
                'color': (255, 255, 0),  # Yellow
                'stroke_color': (0, 0, 0),  # Black
                'stroke_width': 4,
                'font_name': 'arial.ttf'
            },
            'minimal': {
                'fontsize': 50,
                'color': (255, 255, 255),  # White
                'stroke_color': (128, 128, 128),  # Gray
                'stroke_width': 1,
                'font_name': 'arial.ttf'
            }
        }
        
        # Voice settings
        self.voice_settings = {
            'speed': 160,  # Words per minute
            'volume': 0.9,
            'voice_id': 0  # 0 for male, 1 for female (if available)
        }

    def load_content_data(self, file_path):
        """Load motivational content from JSON or CSV file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Content file not found: {file_path}")
        
        content = []
        
        if file_path.endswith('.json'):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
        elif file_path.endswith('.csv'):
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                content = list(reader)
        else:
            raise ValueError("Content file must be JSON or CSV format")
        
        print(f"Loaded {len(content)} content items from {file_path}")
        return content

    def get_font(self, font_name, size):
        """Get font object, with fallbacks"""
        try:
            # Try to load the specified font
            return ImageFont.truetype(font_name, size)
        except:
            try:
                # Try common Windows fonts
                if 'arial' in font_name.lower():
                    return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size)
                elif 'georgia' in font_name.lower():
                    return ImageFont.truetype("C:/Windows/Fonts/georgia.ttf", size)
            except:
                pass
            
            # Fallback to default font
            try:
                return ImageFont.load_default()
            except:
                return None

    def create_text_image(self, text, style_config, width=1080, height=200):
        """Create text image using PIL"""
        # Create image with transparent background
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Get font
        font = self.get_font(style_config['font_name'], style_config['fontsize'])
        if not font:
            # If no font available, create simple text overlay
            return self.create_simple_text_overlay(text, style_config, width, height)
        
        # Wrap text
        wrapped_text = textwrap.fill(text, width=25)
        lines = wrapped_text.split('\n')
        
        # Calculate text positioning
        line_height = style_config['fontsize'] + 10
        total_height = len(lines) * line_height
        y_start = (height - total_height) // 2
        
        # Draw text with stroke
        for i, line in enumerate(lines):
            # Get text size
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            y = y_start + i * line_height
            
            # Draw stroke (outline)
            stroke_width = style_config['stroke_width']
            stroke_color = style_config['stroke_color']
            
            for dx in range(-stroke_width, stroke_width + 1):
                for dy in range(-stroke_width, stroke_width + 1):
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), line, font=font, fill=stroke_color)
            
            # Draw main text
            draw.text((x, y), line, font=font, fill=style_config['color'])
        
        return img

    def create_simple_text_overlay(self, text, style_config, width=1080, height=200):
        """Create simple colored rectangle with text info (fallback)"""
        img = Image.new('RGBA', (width, height), (0, 0, 0, 180))  # Semi-transparent background
        draw = ImageDraw.Draw(img)
        
        # Use basic text (this will be very simple without proper fonts)
        wrapped_text = textwrap.fill(text, width=30)
        lines = wrapped_text.split('\n')
        
        # Draw simple text placeholder
        y_pos = height // 4
        for line in lines[:4]:  # Limit to 4 lines
            draw.text((50, y_pos), line[:50], fill=(255, 255, 255))  # White text
            y_pos += 30
        
        return img

    def generate_voice_over(self, text, output_path, voice_settings=None):
        """Generate voice-over audio from text using pyttsx3"""
        if voice_settings is None:
            voice_settings = self.voice_settings
        
        try:
            # Initialize TTS engine
            engine = pyttsx3.init()
            
            # Set voice properties
            voices = engine.getProperty('voices')
            if voices and len(voices) > voice_settings['voice_id']:
                engine.setProperty('voice', voices[voice_settings['voice_id']].id)
            
            engine.setProperty('rate', voice_settings['speed'])
            engine.setProperty('volume', voice_settings['volume'])
            
            # Save to file
            engine.save_to_file(text, output_path)
            engine.runAndWait()
            
            print(f"✓ Generated voice-over: {os.path.basename(output_path)}")
            return output_path
            
        except Exception as e:
            print(f"Error generating voice-over: {e}")
            # Fallback: create silent audio of estimated duration
            estimated_duration = len(text.split()) / (voice_settings['speed'] / 60)
            silent_audio = AudioClip(lambda t: 0, duration=estimated_duration)
            silent_audio.write_audiofile(output_path, verbose=False, logger=None)
            return output_path

    def create_text_clips_pil(self, text, duration, style='modern', animation='fade'):
        """Create text clips using PIL-generated images"""
        # Break text into chunks for better readability
        words = text.split()
        chunks = []
        
        # Create chunks of 6-8 words each
        chunk_size = 8
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
        
        if not chunks:
            return []
        
        text_clips = []
        chunk_duration = duration / len(chunks)
        
        style_config = self.text_styles.get(style, self.text_styles['modern'])
        
        for i, chunk in enumerate(chunks):
            start_time = i * chunk_duration
            
            # Create text image using PIL
            text_img = self.create_text_image(chunk, style_config, self.target_width, 300)
            
            # Convert PIL image to numpy array
            img_array = np.array(text_img)
            
            # Create ImageClip from array
            img_clip = ImageClip(img_array, duration=chunk_duration, transparent=True)
            img_clip = img_clip.set_position('center').set_start(start_time)
            
            # Add animation effects
            if animation == 'fade':
                if i == 0:
                    img_clip = img_clip.fadein(0.5)
                if i == len(chunks) - 1:
                    img_clip = img_clip.fadeout(0.5)
                else:
                    img_clip = img_clip.fadeout(0.3)
                    
            elif animation == 'slide':
                # Slide in from bottom
                def slide_position(t):
                    if t < 0.5:
                        y_pos = self.target_height - 300 * (t / 0.5)
                    else:
                        y_pos = self.target_height - 300
                    return ('center', y_pos)
                
                img_clip = img_clip.set_position(slide_position)
                    
            elif animation == 'zoom':
                # Zoom in effect
                img_clip = img_clip.resize(lambda t: min(1 + t*0.1, 1.1))
            
            text_clips.append(img_clip)
        
        return text_clips

    def add_subtitle_effect(self, text_clips):
        """Add subtitle-style background to text clips"""
        enhanced_clips = []
        
        for txt_clip in text_clips:
            # Create semi-transparent background
            bg_clip = ColorClip(
                size=(self.target_width, 200),
                color=(0, 0, 0),
                duration=txt_clip.duration
            ).set_opacity(0.6).set_position('center').set_start(txt_clip.start)
            
            enhanced_clips.extend([bg_clip, txt_clip])
        
        return enhanced_clips

    def create_reel(self, background_video_path, content_item, style='modern', 
                   animation='fade', voice_enabled=True, subtitle_bg=True):
        """Create a complete Instagram Reel from background video and content"""
        
        try:
            # Load background video
            print(f"Loading background video: {background_video_path}")
            bg_video = VideoFileClip(background_video_path)
            
            # Prepare text content
            title = content_item.get('title', '')
            content_text = content_item.get('content', '') or content_item.get('full_text', '')
            
            # Combine title and content
            full_text = f"{title}. {content_text}".strip()
            if not full_text:
                raise ValueError("No text content found in content item")
            
            # Clean up text
            full_text = full_text.replace('\n', ' ').replace('  ', ' ')
            
            # Limit text length for better pacing
            max_words = 150  # Approximately 60-90 seconds of speech
            words = full_text.split()
            if len(words) > max_words:
                full_text = ' '.join(words[:max_words]) + '...'
            
            print(f"Processing text: {len(words)} words")
            
            # Generate voice-over if enabled
            audio_clip = None
            if voice_enabled:
                audio_filename = f"voice_{content_item.get('id', 'temp')}_{int(time.time())}.wav"
                audio_path = os.path.join(self.temp_folder, audio_filename)
                
                voice_path = self.generate_voice_over(full_text, audio_path)
                if os.path.exists(voice_path):
                    audio_clip = AudioFileClip(voice_path)
                    print(f"Voice-over duration: {audio_clip.duration:.1f} seconds")
            
            # Determine video duration
            if audio_clip:
                target_duration = audio_clip.duration
            else:
                # Estimate duration based on reading speed (150 WPM)
                word_count = len(full_text.split())
                target_duration = (word_count / 150) * 60
                target_duration = max(30, min(target_duration, 90))  # 30-90 seconds
            
            # Adjust background video duration
            if bg_video.duration > target_duration:
                # Use random segment from background video
                start_time = random.uniform(0, bg_video.duration - target_duration)
                bg_video = bg_video.subclip(start_time, start_time + target_duration)
            else:
                # Loop background video if needed
                bg_video = bg_video.loop(duration=target_duration)
            
            # Create text clips using PIL
            print("Creating text overlays...")
            text_clips = self.create_text_clips_pil(
                full_text, 
                target_duration, 
                style=style, 
                animation=animation
            )
            
            # Add subtitle backgrounds if requested
            if subtitle_bg and text_clips:
                text_clips = self.add_subtitle_effect(text_clips)
            
            # Combine all elements
            final_clips = [bg_video] + text_clips
            
            if audio_clip:
                # Sync audio with video
                final_video = CompositeVideoClip(final_clips, size=(self.target_width, self.target_height))
                final_video = final_video.set_audio(audio_clip)
            else:
                final_video = CompositeVideoClip(final_clips, size=(self.target_width, self.target_height))
            
            # Set final duration
            final_video = final_video.set_duration(target_duration)
            
            return final_video, target_duration
            
        except Exception as e:
            print(f"Error creating reel: {e}")
            return None, 0

    def batch_create_reels(self, background_video_path, content_file, num_reels=5, 
                          style='modern', animation='fade', voice_enabled=True):
        """Create multiple reels from content file"""
        
        # Load content
        content_data = self.load_content_data(content_file)
        
        if len(content_data) < num_reels:
            print(f"Warning: Only {len(content_data)} content items available, creating {len(content_data)} reels")
            num_reels = len(content_data)
        
        # Select random content items
        selected_content = random.sample(content_data, num_reels)
        
        created_reels = []
        
        for i, content_item in enumerate(selected_content, 1):
            print(f"\n--- Creating Reel {i}/{num_reels} ---")
            print(f"Title: {content_item.get('title', 'No title')[:50]}...")
            
            reel, duration = self.create_reel(
                background_video_path,
                content_item,
                style=style,
                animation=animation,
                voice_enabled=voice_enabled
            )
            
            if reel:
                # Generate output filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_title = "".join(c for c in content_item.get('title', 'reel')[:30] 
                                   if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_title = safe_title.replace(' ', '_')
                
                output_filename = f"reel_{i}_{safe_title}_{timestamp}.mp4"
                output_path = os.path.join(self.output_folder, output_filename)
                
                # Export video
                print(f"Exporting reel {i}: {output_filename}")
                reel.write_videofile(
                    output_path,
                    fps=30,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile='temp-audio.m4a',
                    remove_temp=True,
                    preset='medium',
                    ffmpeg_params=[
                        '-crf', '23',
                        '-pix_fmt', 'yuv420p',
                        '-movflags', '+faststart'
                    ],
                    verbose=False,
                    logger=None
                )
                
                created_reels.append({
                    'file': output_path,
                    'title': content_item.get('title', ''),
                    'duration': duration
                })
                
                # Clean up
                reel.close()
                
                print(f"✅ Reel {i} created: {output_filename} ({duration:.1f}s)")
            
            else:
                print(f"❌ Failed to create reel {i}")
        
        return created_reels

    def cleanup_temp_files(self):
        """Clean up temporary audio files"""
        try:
            import time
            time.sleep(2)  # Wait a bit for files to be released
            for file in os.listdir(self.temp_folder):
                if file.endswith(('.wav', '.mp3')):
                    try:
                        os.remove(os.path.join(self.temp_folder, file))
                    except:
                        pass  # File might still be in use
            print("🧹 Cleaned up temporary files")
        except Exception as e:
            print(f"Warning: Could not clean up temp files: {e}")

def main():
    parser = argparse.ArgumentParser(description="Create Instagram Reels with voice-over and text")
    parser.add_argument("--background", "-b", required=True,
                       help="Path to background video file")
    parser.add_argument("--content", "-c", required=True,
                       help="Path to content file (JSON or CSV)")
    parser.add_argument("--num-reels", "-n", type=int, default=3,
                       help="Number of reels to create")
    parser.add_argument("--style", "-s", choices=['modern', 'elegant', 'bold', 'minimal'],
                       default='modern', help="Text style")
    parser.add_argument("--animation", "-a", choices=['fade', 'slide', 'zoom'],
                       default='fade', help="Text animation type")
    parser.add_argument("--voice", action='store_true', default=True,
                       help="Enable voice-over (default: True)")
    parser.add_argument("--no-voice", dest='voice', action='store_false',
                       help="Disable voice-over")
    parser.add_argument("--voice-speed", type=int, default=160,
                       help="Voice speed in WPM (default: 160)")
    
    args = parser.parse_args()
    
    try:
        # Create reel creator
        creator = InstagramReelCreator()
        
        # Update voice settings
        creator.voice_settings['speed'] = args.voice_speed
        
        print("🎬 Instagram Reel Creator Started")
        print(f"Background Video: {args.background}")
        print(f"Content Source: {args.content}")
        print(f"Number of Reels: {args.num_reels}")
        print(f"Style: {args.style}")
        print(f"Animation: {args.animation}")
        print(f"Voice-over: {'Enabled' if args.voice else 'Disabled'}")
        
        # Create reels
        created_reels = creator.batch_create_reels(
            background_video_path=args.background,
            content_file=args.content,
            num_reels=args.num_reels,
            style=args.style,
            animation=args.animation,
            voice_enabled=args.voice
        )
        
        # Clean up
        creator.cleanup_temp_files()
        
        # Summary
        print(f"\n🎉 Successfully created {len(created_reels)} Instagram Reels!")
        print(f"📁 Output folder: {creator.output_folder}")
        
        total_duration = sum(reel['duration'] for reel in created_reels)
        print(f"⏱️  Total content duration: {total_duration:.1f} seconds")
        
        print("\nCreated Reels:")
        for reel in created_reels:
            print(f"  • {os.path.basename(reel['file'])} ({reel['duration']:.1f}s)")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())