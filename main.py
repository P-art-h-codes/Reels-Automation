#!/usr/bin/env python3
"""
Instagram Reel Creation Pipeline - Main Controller
A comprehensive script that orchestrates background video creation, content scraping, and reel generation.
"""

import os
import sys
import time
import argparse
import json
from datetime import datetime
from pathlib import Path
import subprocess
from typing import Dict, List, Optional

# Import our custom modules
try:
    from background import InstagramBGCreator
    from contentScraper import RedditMotivationalScraper
    from reelCreator import InstagramReelCreator
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Make sure background.py, contentScraper.py, and reelCreator.py are in the same directory")
    sys.exit(1)

class InstagramReelPipeline:
    """Main pipeline controller for Instagram Reel creation"""
    
    def __init__(self, config: Dict):
        """Initialize the pipeline with configuration"""
        self.config = config
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_base = Path(config.get('output_folder', 'instagram_pipeline_output'))
        
        # Create session folder
        self.session_folder = self.output_base / f"session_{self.session_id}"
        self.session_folder.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.bg_creator = None
        self.content_scraper = None
        self.reel_creator = None
        
        print(f"🚀 Instagram Reel Pipeline Initialized")
        print(f"📁 Session folder: {self.session_folder}")
        
    def step_1_create_background_video(self) -> Optional[Path]:
        """Step 1: Create background video"""
        print("\n" + "="*60)
        print("STEP 1: CREATING BACKGROUND VIDEO")
        print("="*60)
        
        try:
            # Initialize background creator
            stock_folder = self.config.get('stock_videos_folder', 'StockVideos')
            bg_output_folder = self.session_folder / 'backgrounds'
            
            self.bg_creator = InstagramBGCreator(
                stock_folder=stock_folder,
                output_folder=str(bg_output_folder)
            )
            
            # Background video configuration
            bg_config = self.config.get('background', {})
            
            background_path = self.bg_creator.create_background_video(
                duration=bg_config.get('duration', 120),  # 2 minutes default
                num_clips=bg_config.get('num_clips', None),
                effect_type=bg_config.get('effect_type', 'cinematic'),
                transition_duration=bg_config.get('transition_duration', 1.5),
                transition_type=bg_config.get('transition_type', 'crossfade'),
                output_name=f"background_{self.session_id}.mp4"
            )
            
            print(f"✅ Background video created: {background_path}")
            return Path(background_path)
            
        except Exception as e:
            print(f"❌ Background video creation failed: {e}")
            return None
    
    def step_2_scrape_content(self) -> Optional[Path]:
        """Step 2: Scrape motivational content from Reddit"""
        print("\n" + "="*60)
        print("STEP 2: SCRAPING CONTENT FROM REDDIT")
        print("="*60)
        
        try:
            # Check for Reddit credentials
            client_id = os.getenv('REDDIT_CLIENT_ID')
            client_secret = os.getenv('REDDIT_CLIENT_SECRET')
            user_agent = self.config.get('reddit', {}).get('user_agent', 
                                        "InstagramReelPipeline/1.0 by ReelCreator")
            
            if not client_id or not client_secret:
                print("⚠️ Reddit API credentials not found in environment variables")
                print("Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET")
                
                # Try to use existing content file if specified
                existing_content = self.config.get('existing_content_file')
                if existing_content and Path(existing_content).exists():
                    print(f"📄 Using existing content file: {existing_content}")
                    return Path(existing_content)
                else:
                    print("❌ No existing content file found")
                    return None
            
            # Initialize content scraper
            self.content_scraper = RedditMotivationalScraper(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            
            # Content scraping configuration
            content_config = self.config.get('content', {})
            
            # Define subreddits to scrape
            subreddits = content_config.get('subreddits', [
                'GetMotivated', 'motivation', 'wholesomememes', 'LifeProTips',
                'decidingtobebetter', 'selfimprovement', 'quotes', 'productivity'
            ])
            
            # Scrape content
            posts = self.content_scraper.scrape_multiple_subreddits(
                subreddits=subreddits,
                posts_per_sub=content_config.get('posts_per_sub', 25),
                min_time=content_config.get('min_reading_time', 30),
                max_time=content_config.get('max_reading_time', 180)
            )
            
            if not posts:
                print("❌ No suitable content found")
                return None
            
            # Sort posts by score and reading time
            posts.sort(key=lambda x: (x['score'], -abs(x['reading_time_seconds'] - 90)), 
                      reverse=True)
            
            # Save content
            content_file = self.session_folder / f"content_{self.session_id}.json"
            self.content_scraper.save_to_json(posts, str(content_file))
            
            # Also save CSV for easy viewing
            csv_file = self.session_folder / f"content_{self.session_id}.csv"
            self.content_scraper.save_to_csv(posts, str(csv_file))
            
            print(f"✅ Content scraped and saved: {content_file}")
            print(f"📊 Found {len(posts)} suitable posts")
            
            return content_file
            
        except Exception as e:
            print(f"❌ Content scraping failed: {e}")
            return None
    
    def step_3_create_reels(self, background_video: Path, content_file: Path) -> List[Path]:
        """Step 3: Create Instagram Reels"""
        print("\n" + "="*60)
        print("STEP 3: CREATING INSTAGRAM REELS")
        print("="*60)
        
        created_reels = []
        
        try:
            # Initialize reel creator
            reel_output_folder = self.session_folder / 'reels'
            self.reel_creator = InstagramReelCreator(output_folder=str(reel_output_folder))
            
            # Reel creation configuration
            reel_config = self.config.get('reels', {})
            
            # Create reels
            reels = self.reel_creator.create_batch_reels(
                background_video=str(background_video),
                content_file=str(content_file),
                num_reels=reel_config.get('num_reels', 5),
                lang=reel_config.get('language', 'a'),
                voice=reel_config.get('voice', 'af_heart'),
                style=reel_config.get('text_style', 'modern'),
                animation=reel_config.get('text_animation', 'fade'),
                voice_speed=reel_config.get('voice_speed', 1.0),
                max_duration=reel_config.get('max_duration', 90)
            )
            
            for reel in reels:
                created_reels.append(reel['file'])
                print(f"✅ Created: {reel['file'].name}")
            
            return created_reels
            
        except Exception as e:
            print(f"❌ Reel creation failed: {e}")
            return []
    
    def run_pipeline(self) -> Dict:
        """Run the complete pipeline"""
        start_time = time.time()
        results = {
            'session_id': self.session_id,
            'session_folder': str(self.session_folder),
            'success': False,
            'background_video': None,
            'content_file': None,
            'created_reels': [],
            'errors': [],
            'processing_time': 0
        }
        
        print("🎬 Starting Instagram Reel Creation Pipeline")
        print(f"Session ID: {self.session_id}")
        
        try:
            # Step 1: Create background video
            if self.config.get('skip_background', False):
                # Use existing background video
                background_path = Path(self.config.get('existing_background_video'))
                if not background_path.exists():
                    raise FileNotFoundError(f"Background video not found: {background_path}")
                print(f"📹 Using existing background: {background_path}")
            else:
                background_path = self.step_1_create_background_video()
                if not background_path:
                    results['errors'].append("Background video creation failed")
                    return results
            
            results['background_video'] = str(background_path)
            
            # Step 2: Scrape content
            if self.config.get('skip_scraping', False):
                # Use existing content file
                content_path = Path(self.config.get('existing_content_file'))
                if not content_path.exists():
                    raise FileNotFoundError(f"Content file not found: {content_path}")
                print(f"📄 Using existing content: {content_path}")
            else:
                content_path = self.step_2_scrape_content()
                if not content_path:
                    results['errors'].append("Content scraping failed")
                    return results
            
            results['content_file'] = str(content_path)
            
            # Step 3: Create reels
            created_reels = self.step_3_create_reels(background_path, content_path)
            if not created_reels:
                results['errors'].append("Reel creation failed")
                return results
            
            results['created_reels'] = [str(reel) for reel in created_reels]
            results['success'] = True
            
            # Save session summary
            self.save_session_summary(results)
            
        except Exception as e:
            results['errors'].append(str(e))
            print(f"❌ Pipeline error: {e}")
        
        finally:
            results['processing_time'] = time.time() - start_time
            
            # Cleanup
            if self.reel_creator:
                self.reel_creator.cleanup()
        
        return results
    
    def save_session_summary(self, results: Dict):
        """Save session summary to JSON file"""
        summary_file = self.session_folder / 'session_summary.json'
        
        summary = {
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'config': self.config,
            'results': results
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Session summary saved: {summary_file}")
    
    def print_final_summary(self, results: Dict):
        """Print final pipeline summary"""
        print("\n" + "="*60)
        print("🎉 PIPELINE SUMMARY")
        print("="*60)
        
        if results['success']:
            print(f"✅ Pipeline completed successfully!")
            print(f"⏱️  Total processing time: {results['processing_time']:.1f}s")
            print(f"📁 Session folder: {results['session_folder']}")
            print(f"📹 Background video: {Path(results['background_video']).name}")
            print(f"📄 Content file: {Path(results['content_file']).name}")
            print(f"🎬 Created reels: {len(results['created_reels'])}")
            
            if results['created_reels']:
                print("\nCreated Reel Files:")
                for reel_path in results['created_reels']:
                    print(f"  📱 {Path(reel_path).name}")
            
            print(f"\n📋 Full results saved in: {results['session_folder']}")
        else:
            print("❌ Pipeline failed!")
            print(f"⏱️  Processing time: {results['processing_time']:.1f}s")
            
            if results['errors']:
                print("\nErrors encountered:")
                for error in results['errors']:
                    print(f"  ❌ {error}")

def create_default_config() -> Dict:
    """Create default configuration"""
    return {
        'output_folder': 'instagram_pipeline_output',
        'stock_videos_folder': 'StockVideos',
        'skip_background': False,
        'skip_scraping': False,
        'existing_background_video': None,
        'existing_content_file': None,
        
        'background': {
            'duration': 120,
            'num_clips': None,
            'effect_type': 'cinematic',
            'transition_duration': 1.5,
            'transition_type': 'crossfade'
        },
        
        'content': {
            'subreddits': [
                'GetMotivated', 'motivation', 'wholesomememes', 'LifeProTips',
                'decidingtobebetter', 'selfimprovement', 'quotes', 'productivity',
                'findapath', 'UpliftingNews'
            ],
            'posts_per_sub': 25,
            'min_reading_time': 30,
            'max_reading_time': 180
        },
        
        'reddit': {
            'user_agent': 'InstagramReelPipeline/1.0 by ReelCreator'
        },
        
        'reels': {
            'num_reels': 5,
            'language': 'a',
            'voice': 'af_heart',
            'text_style': 'modern',
            'text_animation': 'fade',
            'voice_speed': 1.0,
            'max_duration': 90
        }
    }

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Instagram Reel Creation Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Pipeline Steps:
  1. Create background video from stock footage
  2. Scrape motivational content from Reddit
  3. Generate Instagram Reels with TTS voiceover

Configuration:
  Use --config to specify a JSON configuration file
  Or use individual options to customize each step

Environment Variables Required:
  REDDIT_CLIENT_ID     - Reddit API client ID
  REDDIT_CLIENT_SECRET - Reddit API client secret

Examples:
  # Full pipeline with defaults
  python main.py
  
  # Custom configuration
  python main.py --num-reels 10 --voice bf_emma --effect-type warm
  
  # Skip background creation, use existing video
  python main.py --existing-bg video.mp4 --skip-background
  
  # Use configuration file
  python main.py --config my_config.json

Available Voices:
  af_heart, af_bella, af_sarah, af_nicole  (American Female)
  am_adam, am_michael                      (American Male)
  bf_emma, bf_isabella                     (British Female)
  bm_lewis, bm_george                      (British Male)
        """
    )
    
    # Configuration options
    parser.add_argument('--config', type=str, 
                       help='JSON configuration file path')
    parser.add_argument('--output-folder', type=str, default='instagram_pipeline_output',
                       help='Output folder for all generated files')
    parser.add_argument('--stock-folder', type=str, default='StockVideos',
                       help='Folder containing stock videos')
    
    # Background video options
    bg_group = parser.add_argument_group('Background Video Options')
    bg_group.add_argument('--skip-background', action='store_true',
                         help='Skip background creation, use existing video')
    bg_group.add_argument('--existing-bg', type=str,
                         help='Path to existing background video')
    bg_group.add_argument('--bg-duration', type=int, default=120,
                         help='Background video duration in seconds')
    bg_group.add_argument('--effect-type', choices=['subtle', 'cinematic', 'warm', 'cool'],
                         default='cinematic', help='Background effect type')
    bg_group.add_argument('--transition-type', choices=['crossfade', 'slide', 'zoom'],
                         default='crossfade', help='Background transition type')
    
    # Content scraping options
    content_group = parser.add_argument_group('Content Scraping Options')
    content_group.add_argument('--skip-scraping', action='store_true',
                              help='Skip content scraping, use existing file')
    content_group.add_argument('--existing-content', type=str,
                              help='Path to existing content file (JSON/CSV)')
    content_group.add_argument('--posts-per-sub', type=int, default=25,
                              help='Number of posts to fetch per subreddit')
    content_group.add_argument('--min-time', type=int, default=30,
                              help='Minimum reading time in seconds')
    content_group.add_argument('--max-time', type=int, default=180,
                              help='Maximum reading time in seconds')
    
    # Reel creation options
    reel_group = parser.add_argument_group('Reel Creation Options')
    reel_group.add_argument('--num-reels', type=int, default=5,
                           help='Number of reels to create')
    reel_group.add_argument('--voice', default='af_heart',
                           help='TTS voice to use')
    reel_group.add_argument('--voice-speed', type=float, default=1.0,
                           help='Voice speed multiplier (0.5-2.0)')
    reel_group.add_argument('--text-style', choices=['modern', 'elegant', 'bold', 'minimal', 'vibrant'],
                           default='modern', help='Text overlay style')
    reel_group.add_argument('--text-animation', choices=['fade', 'slide', 'zoom'],
                           default='fade', help='Text animation type')
    reel_group.add_argument('--max-duration', type=int, default=90,
                           help='Maximum reel duration in seconds')
    
    # Utility options
    parser.add_argument('--create-config', type=str,
                       help='Create a default configuration file and exit')
    parser.add_argument('--list-voices', action='store_true',
                       help='List available TTS voices and exit')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show configuration and exit without processing')
    
    args = parser.parse_args()
    
    try:
        # Handle utility options
        if args.list_voices:
            creator = InstagramReelCreator()
            creator.list_voices()
            return 0
        
        if args.create_config:
            config = create_default_config()
            config_path = Path(args.create_config)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            print(f"✅ Default configuration created: {config_path}")
            return 0
        
        # Load or create configuration
        if args.config:
            config_path = Path(args.config)
            if not config_path.exists():
                print(f"❌ Configuration file not found: {config_path}")
                return 1
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"📄 Loaded configuration from: {config_path}")
        else:
            config = create_default_config()
        
        # Override config with command line arguments
        config['output_folder'] = args.output_folder
        config['stock_videos_folder'] = args.stock_folder
        config['skip_background'] = args.skip_background
        config['skip_scraping'] = args.skip_scraping
        config['existing_background_video'] = args.existing_bg
        config['existing_content_file'] = args.existing_content
        
        # Background options
        config['background'].update({
            'duration': args.bg_duration,
            'effect_type': args.effect_type,
            'transition_type': args.transition_type
        })
        
        # Content options
        config['content'].update({
            'posts_per_sub': args.posts_per_sub,
            'min_reading_time': args.min_time,
            'max_reading_time': args.max_time
        })
        
        # Reel options
        config['reels'].update({
            'num_reels': args.num_reels,
            'voice': args.voice,
            'voice_speed': args.voice_speed,
            'text_style': args.text_style,
            'text_animation': args.text_animation,
            'max_duration': args.max_duration
        })
        
        # Validation
        if config['skip_background'] and not config.get('existing_background_video'):
            print("❌ Error: --existing-bg required when using --skip-background")
            return 1
        
        if config['skip_scraping'] and not config.get('existing_content_file'):
            print("❌ Error: --existing-content required when using --skip-scraping")
            return 1
        
        # Show configuration
        print("🔧 PIPELINE CONFIGURATION")
        print("="*50)
        print(f"Output Folder: {config['output_folder']}")
        print(f"Stock Videos: {config['stock_videos_folder']}")
        print(f"Skip Background: {config['skip_background']}")
        print(f"Skip Scraping: {config['skip_scraping']}")
        print(f"Number of Reels: {config['reels']['num_reels']}")
        print(f"TTS Voice: {config['reels']['voice']}")
        print(f"Text Style: {config['reels']['text_style']}")
        print("="*50)
        
        if args.dry_run:
            print("🔍 Dry run completed. Configuration looks good!")
            return 0
        
        # Initialize and run pipeline
        pipeline = InstagramReelPipeline(config)
        results = pipeline.run_pipeline()
        
        # Print final summary
        pipeline.print_final_summary(results)
        
        return 0 if results['success'] else 1
        
    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())