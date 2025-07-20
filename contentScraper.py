import praw
import json
import csv
import time
from datetime import datetime
import re
import os
import dotenv
# Load environment variables from .env file
dotenv.load_dotenv()

class RedditMotivationalScraper:
    def __init__(self, client_id, client_secret, user_agent):
        """
        Initialize the Reddit scraper with API credentials
        
        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: User agent string for API requests
        """
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        
    def estimate_reading_time(self, text, wpm=200):
        """
        Estimate reading time for text (default 200 words per minute)
        
        Args:
            text: Text content to analyze
            wpm: Words per minute reading speed
            
        Returns:
            Reading time in seconds
        """
        word_count = len(text.split())
        reading_time_minutes = word_count / wpm
        return reading_time_minutes * 60
    
    def clean_text(self, text):
        """
        Clean and format text content
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text
        """
        # Remove Reddit markdown and special characters
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
        text = re.sub(r'~~(.*?)~~', r'\1', text)      # Strikethrough
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)  # Links
        text = re.sub(r'&gt;', '>', text)             # Quote markers
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'\n+', ' ', text)              # Multiple newlines
        text = text.strip()
        return text
    
    def scrape_subreddit(self, subreddit_name, limit=50, time_filter='week', 
                        min_time=60, max_time=120):
        """
        Scrape motivational content from a specific subreddit
        
        Args:
            subreddit_name: Name of subreddit to scrape
            limit: Maximum number of posts to fetch
            time_filter: Time filter (hour, day, week, month, year, all)
            min_time: Minimum reading time in seconds
            max_time: Maximum reading time in seconds (90 seconds default range)
            
        Returns:
            List of filtered posts
        """
        print(f"Scraping r/{subreddit_name}...")
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            posts = []
            
            # Get top posts from the specified time period
            for submission in subreddit.top(time_filter=time_filter, limit=limit):
                # Skip stickied posts and deleted content
                if submission.stickied or not submission.selftext:
                    continue
                
                # Clean the content
                title = self.clean_text(submission.title)
                content = self.clean_text(submission.selftext)
                full_text = f"{title}. {content}"
                
                # Check reading time
                reading_time = self.estimate_reading_time(full_text)
                
                if min_time <= reading_time <= max_time:
                    post_data = {
                        'title': title,
                        'content': content,
                        'full_text': full_text,
                        'author': str(submission.author) if submission.author else 'Unknown',
                        'score': submission.score,
                        'url': f"https://reddit.com{submission.permalink}",
                        'created_utc': submission.created_utc,
                        'reading_time_seconds': round(reading_time, 1),
                        'subreddit': subreddit_name,
                        'id': submission.id
                    }
                    posts.append(post_data)
                    print(f"✓ Found story: '{title[:50]}...' ({reading_time:.1f}s read)")
                
                # Rate limiting
                time.sleep(0.1)
                
        except Exception as e:
            print(f"Error scraping r/{subreddit_name}: {e}")
            
        return posts
    
    def scrape_multiple_subreddits(self, subreddits, posts_per_sub=25, 
                                 min_time=60, max_time=120):
        """
        Scrape from multiple subreddits
        
        Args:
            subreddits: List of subreddit names
            posts_per_sub: Number of posts to fetch per subreddit
            min_time: Minimum reading time in seconds
            max_time: Maximum reading time in seconds
            
        Returns:
            Combined list of posts from all subreddits
        """
        all_posts = []
        
        for subreddit in subreddits:
            posts = self.scrape_subreddit(
                subreddit, 
                limit=posts_per_sub, 
                min_time=min_time, 
                max_time=max_time
            )
            all_posts.extend(posts)
            print(f"Found {len(posts)} suitable posts in r/{subreddit}")
            
            # Rate limiting between subreddits
            time.sleep(1)
            
        return all_posts
    
    def save_to_json(self, posts, filename):
        """Save posts to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(posts)} posts to {filename}")
    
    def save_to_csv(self, posts, filename):
        """Save posts to CSV file"""
        if not posts:
            print("No posts to save")
            return
            
        fieldnames = posts[0].keys()
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(posts)
        print(f"Saved {len(posts)} posts to {filename}")

def main():
    # Reddit API credentials (you need to get these from Reddit)
    CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
    USER_AGENT = "MotivationalScraper/1.0 by YourUsername"
    
    # Initialize scraper
    scraper = RedditMotivationalScraper(CLIENT_ID, CLIENT_SECRET, USER_AGENT)
    
    # Subreddits known for motivational content
    motivational_subreddits = [
        'GetMotivated',
        'motivation',
        'wholesomememes',
        'LifeProTips',
        'decidingtobebetter',
        'selfimprovement',
        'quotes',
        'productivity',
        'findapath',
        'UpliftingNews'
    ]
    
    print("Starting Reddit motivational content scraper...")
    print(f"Target reading time: 60-120 seconds (90 second range)")
    
    # Scrape posts (looking for 60-120 second reads, which covers your 90 second target)
    posts = scraper.scrape_multiple_subreddits(
        subreddits=motivational_subreddits,
        posts_per_sub=20,  # Fetch 20 posts per subreddit
        min_time=60,       # 1 minute minimum
        max_time=120       # 2 minute maximum (covers 90 seconds)
    )
    
    # Sort by score (popularity) and reading time
    posts.sort(key=lambda x: (x['score'], -abs(x['reading_time_seconds'] - 90)), reverse=True)
    
    print(f"\nFound {len(posts)} motivational stories/quotes in the 60-120 second range")
    
    if posts:
        # Create timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save results
        scraper.save_to_json(posts, f"motivational_content_{timestamp}.json")
        scraper.save_to_csv(posts, f"motivational_content_{timestamp}.csv")
        
        # Display some statistics
        avg_reading_time = sum(p['reading_time_seconds'] for p in posts) / len(posts)
        print(f"Average reading time: {avg_reading_time:.1f} seconds")
        print(f"Range: {min(p['reading_time_seconds'] for p in posts):.1f}s - {max(p['reading_time_seconds'] for p in posts):.1f}s")
        
        # Show top 3 posts
        print("\nTop 3 posts by score:")
        for i, post in enumerate(posts[:3], 1):
            print(f"{i}. '{post['title'][:60]}...' ({post['reading_time_seconds']}s, {post['score']} upvotes)")
    
    else:
        print("No suitable posts found. Try adjusting the time range or subreddits.")

if __name__ == "__main__":
    main()