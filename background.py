import os
import random
from moviepy.editor import *
from moviepy.video.fx import resize, fadein, fadeout
from moviepy.video.fx.all import colorx
import numpy as np
from datetime import datetime
import argparse

class InstagramBGCreator:
    def __init__(self, stock_folder="StockVideos", output_folder="output"):
        self.stock_folder = stock_folder
        self.output_folder = output_folder
        self.target_width = 1080
        self.target_height = 1920  # 9:16 aspect ratio
        self.supported_formats = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm')
        
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
    
    def get_video_files(self):
        """Get all video files from the stock folder"""
        video_files = []
        
        if not os.path.exists(self.stock_folder):
            raise FileNotFoundError(f"Stock folder '{self.stock_folder}' not found!")
        
        for file in os.listdir(self.stock_folder):
            if file.lower().endswith(self.supported_formats):
                video_files.append(os.path.join(self.stock_folder, file))
        
        if not video_files:
            raise ValueError(f"No video files found in '{self.stock_folder}' folder!")
        
        return video_files
    
    def crop_to_vertical(self, clip):
        """
        Crop video to 9:16 aspect ratio maintaining quality
        Uses center crop with option to focus on most interesting part
        """
        w, h = clip.w, clip.h
        
        # Calculate target dimensions based on current video
        if w / h > 9/16:  # Video is too wide
            # Crop width, keep full height
            new_width = int(h * 9/16)
            x_center = w // 2
            x1 = max(0, x_center - new_width // 2)
            x2 = min(w, x1 + new_width)
            clip = clip.crop(x1=x1, x2=x2)
        else:  # Video is too tall or perfect ratio
            # Crop height, keep full width  
            new_height = int(w * 16/9)
            y_center = h // 2
            y1 = max(0, y_center - new_height // 2)
            y2 = min(h, y1 + new_height)
            clip = clip.crop(y1=y1, y2=y2)
        
        # Resize to exact Instagram dimensions
        clip = clip.resize((self.target_width, self.target_height))
        return clip
    
    def add_aesthetic_effects(self, clip, effect_type="subtle"):
        """
        Add aesthetic effects to enhance the video
        """
        if effect_type == "cinematic":
            # Slightly desaturated, film-like look
            clip = clip.fx(colorx, 0.9)  # Slight desaturation
            # Add subtle vignette effect using a mask
            def vignette(get_frame, t):
                frame = get_frame(t)
                h, w = frame.shape[:2]
                
                # Create vignette mask
                Y, X = np.ogrid[:h, :w]
                center_x, center_y = w/2, h/2
                mask = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
                mask = mask / mask.max()
                mask = 1 - mask * 0.3  # Subtle vignette
                mask = np.clip(mask, 0.7, 1)
                
                # Apply vignette
                if len(frame.shape) == 3:
                    mask = mask[:, :, np.newaxis]
                return frame * mask
            
            clip = clip.fl(vignette, apply_to=['mask'])
            
        elif effect_type == "warm":
            # Warm, cozy feeling
            clip = clip.fx(colorx, 1.1)  # Slight saturation boost
            
        elif effect_type == "cool":
            # Cool, modern feeling
            clip = clip.fx(colorx, 0.8)  # Desaturated
            
        return clip
    
    def create_smooth_transition(self, clip1, clip2, transition_duration=1.0, transition_type="crossfade"):
        """
        Create smooth transitions between clips
        """
        if transition_type == "crossfade":
            # Standard crossfade
            clip1 = clip1.fadeout(transition_duration)
            clip2 = clip2.fadein(transition_duration)
            
        elif transition_type == "slide":
            # Slide transition (more complex, simplified version)
            clip1 = clip1.fadeout(transition_duration * 0.5)
            clip2 = clip2.fadein(transition_duration * 0.5)
            
        elif transition_type == "zoom":
            # Subtle zoom effect during transition
            zoom_factor = 1.1
            clip1_end = clip1.fx(resize, lambda t: 1 + (zoom_factor-1) * t/clip1.duration)
            clip1 = clip1_end.fadeout(transition_duration)
            clip2 = clip2.fadein(transition_duration)
        
        return clip1, clip2
    
    def process_clip(self, video_path, segment_duration, start_time=None, effect_type="subtle"):
        """
        Process individual video clip
        """
        try:
            # Load video
            clip = VideoFileClip(video_path)
            
            # If start_time not specified, pick random start point
            if start_time is None:
                max_start = max(0, clip.duration - segment_duration)
                start_time = random.uniform(0, max_start) if max_start > 0 else 0
            
            # Extract segment
            end_time = min(start_time + segment_duration, clip.duration)
            clip = clip.subclip(start_time, end_time)
            
            # Crop to 9:16
            clip = self.crop_to_vertical(clip)
            
            # Add aesthetic effects
            clip = self.add_aesthetic_effects(clip, effect_type)
            
            # Ensure consistent framerate
            clip = clip.set_fps(30)
            
            return clip
            
        except Exception as e:
            print(f"Error processing {video_path}: {e}")
            return None
    
    def create_background_video(self, duration=60, num_clips=None, effect_type="cinematic", 
                              transition_duration=1.5, transition_type="crossfade", 
                              output_name=None):
        """
        Create final background video by combining multiple clips
        
        Args:
            duration: Total duration of final video in seconds
            num_clips: Number of clips to use (if None, auto-calculate)
            effect_type: Type of aesthetic effect ('subtle', 'cinematic', 'warm', 'cool')
            transition_duration: Duration of transitions between clips
            transition_type: Type of transition ('crossfade', 'slide', 'zoom')
            output_name: Custom output filename
        """
        
        video_files = self.get_video_files()
        print(f"Found {len(video_files)} video files")
        
        # Calculate number of clips needed
        if num_clips is None:
            # Estimate: each clip ~8-12 seconds with transitions
            avg_clip_duration = 10
            num_clips = max(3, int(duration / avg_clip_duration))
        
        num_clips = min(num_clips, len(video_files))  # Can't use more clips than available
        
        # Select random videos
        selected_videos = random.sample(video_files, num_clips)
        segment_duration = duration / num_clips + transition_duration  # Overlap for transitions
        
        print(f"Creating {duration}s video using {num_clips} clips...")
        print(f"Effect: {effect_type}, Transition: {transition_type}")
        
        clips = []
        
        # Process each clip
        for i, video_path in enumerate(selected_videos):
            print(f"Processing clip {i+1}/{num_clips}: {os.path.basename(video_path)}")
            
            clip = self.process_clip(
                video_path, 
                segment_duration, 
                effect_type=effect_type
            )
            
            if clip:
                clips.append(clip)
            else:
                print(f"Skipping problematic clip: {video_path}")
        
        if not clips:
            raise ValueError("No clips could be processed successfully!")
        
        # Create transitions and concatenate
        final_clips = []
        
        for i, clip in enumerate(clips):
            if i == 0:
                # First clip - just fade in
                clip = clip.fadein(0.5)
                final_clips.append(clip)
            else:
                # Apply transition with previous clip
                prev_clip = final_clips[-1]
                prev_clip, clip = self.create_smooth_transition(
                    prev_clip, clip, transition_duration, transition_type
                )
                final_clips[-1] = prev_clip  # Update previous clip
                final_clips.append(clip)
        
        # Concatenate all clips
        print("Concatenating clips...")
        final_video = concatenate_videoclips(final_clips, method="compose")
        
        # Trim to exact duration and add final fade out
        final_video = final_video.subclip(0, min(duration, final_video.duration))
        final_video = final_video.fadeout(0.5)
        
        # Generate output filename
        if output_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"instagram_bg_{effect_type}_{duration}s_{timestamp}.mp4"
        
        if not output_name.endswith('.mp4'):
            output_name += '.mp4'
        
        output_path = os.path.join(self.output_folder, output_name)
        
        # Export with optimized settings for Instagram
        print(f"Exporting to {output_path}...")
        final_video.write_videofile(
            output_path,
            fps=30,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            preset='medium',
            ffmpeg_params=[
                '-crf', '23',  # Good quality
                '-pix_fmt', 'yuv420p',  # Instagram compatibility
                '-movflags', '+faststart'  # Web optimization
            ]
        )
        
        # Clean up
        final_video.close()
        for clip in clips:
            clip.close()
        
        print(f"✅ Background video created successfully: {output_path}")
        print(f"Duration: {duration}s, Resolution: {self.target_width}x{self.target_height}")
        
        return output_path

def main():
    parser = argparse.ArgumentParser(description="Create Instagram reel background videos")
    parser.add_argument("--duration", "-d", type=int, default=60, 
                       help="Duration of output video in seconds (default: 60)")
    parser.add_argument("--clips", "-c", type=int, default=None,
                       help="Number of clips to use (default: auto)")
    parser.add_argument("--effect", "-e", choices=['subtle', 'cinematic', 'warm', 'cool'], 
                       default='cinematic', help="Aesthetic effect type")
    parser.add_argument("--transition", "-t", choices=['crossfade', 'slide', 'zoom'],
                       default='crossfade', help="Transition type")
    parser.add_argument("--transition-duration", type=float, default=1.5,
                       help="Transition duration in seconds")
    parser.add_argument("--stock-folder", default="StockVideos",
                       help="Folder containing stock videos")
    parser.add_argument("--output", "-o", default=None,
                       help="Output filename")
    
    args = parser.parse_args()
    
    try:
        # Create background video generator
        bg_creator = InstagramBGCreator(stock_folder=args.stock_folder)
        
        # Generate background video
        output_path = bg_creator.create_background_video(
            duration=args.duration,
            num_clips=args.clips,
            effect_type=args.effect,
            transition_duration=args.transition_duration,
            transition_type=args.transition,
            output_name=args.output
        )
        
        print(f"\n🎉 Success! Your Instagram background video is ready:")
        print(f"📁 {output_path}")
        print(f"📱 Perfect for Instagram Reels (1080x1920, 9:16 ratio)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    # You can also run it directly with default settings
    if len(os.sys.argv) == 1:
        print("Creating Instagram background video with default settings...")
        print("Use --help to see all options\n")
        
        bg_creator = InstagramBGCreator()
        try:
            bg_creator.create_background_video(
                duration=60,
                effect_type="cinematic",
                transition_type="crossfade"
            )
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        exit(main())