from tweeterpy import TweeterPy
from tweeterpy.util import Tweet, User, find_nested_key
from datetime import datetime
import csv
import os
import re


def parse_twitter_date(date_str):
    try:
        return datetime.strptime(date_str, "%a %b %d %H:%M:%S %z %Y")
    except:
        return datetime.min


def extract_emojis(text):
    """Extract emojis from text and convert to unicode-escape format like \\U0001F600"""
    if not text or not isinstance(text, str):
        return []
    try:
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        emojis = emoji_pattern.findall(text)
        # Convert to unicode-escape format (to follow Selenium version)
        result = []
        for emoji in emojis:
            for char in emoji:
                # Format as \U0001F600 (uppercase, 8 digits)
                unicode_escaped = f"\\U{ord(char):08X}"
                result.append(unicode_escaped)
        return result
    except Exception:
        return []


def main():
    # Configuration: Number of tweets to extract per user (can be 100-1000+)
    TWEETS_PER_USER = 10
    
    twitter = TweeterPy(log_level="INFO")
    
    # Login with auth token (get from browser cookies: F12 > Application > Cookies > auth_token)
    auth_token = "14dc1c7fbda5b9cbc54d5538d7db8fc07faf6fc0"
    if auth_token:
        try:
            twitter.generate_session(auth_token=auth_token)
            print("✓ Logged in")
        except Exception as e:
            print(f"Login failed: {e}")
    
    # Read usernames from file
    users_file = 'users.txt'
    try:
        with open(users_file, 'r', encoding='utf-8') as f:
            usernames = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    except FileNotFoundError:
        print(f"Error: {users_file} not found. Create it with one username per line.")
        return
    
    if not usernames:
        print(f"No usernames found in {users_file}")
        return
    
    # Process each user
    for username in usernames:
        print(f"\nScraping @{username}...")
        
        # Get user data using User dataclass (docs.md recommended way)
        try:
            user_data = twitter.get_user_data(username)
            user = User(user_data)
            user_dict = user.dict()
            user_name = user_dict.get('name', '')
            user_screen_name = user_dict.get('screen_name', username)
            user_verified = user_dict.get('verified', False) or user_dict.get('is_blue_verified', False)
            
            # Extract profile image - try User dataclass first, then find_nested_key
            user_profile_image = user_dict.get('profile_image_url_https', '')
            if not user_profile_image:
                # Use find_nested_key to search anywhere in user_data (docs.md pattern)
                try:
                    found = find_nested_key(user_data, "profile_image_url_https")
                    if found:
                        user_profile_image = found if isinstance(found, str) else (found[0] if isinstance(found, list) and found else '')
                except:
                    pass
        except Exception as e:
            print(f"Warning: Could not get user data: {e}")
            user_name = ''
            user_screen_name = username
            user_verified = False
            user_profile_image = ''
        
        tweets = twitter.get_user_tweets(username, total=TWEETS_PER_USER)
        if not tweets or not tweets.get('data'):
            print(f"No tweets found for @{username}")
            continue
        
        # Sort by date (newest first)
        tweet_objects = []
        for tweet_data in tweets['data']:
            try:
                tweet = Tweet(tweet_data)
                tweet_dict = tweet.dict()
                created_at = tweet_dict.get('created_at', '')
                if created_at:
                    # Profile image - use user data (since we're scraping one user's tweets)
                    tweet_dict['profile_image'] = user_profile_image
                    tweet_objects.append((parse_twitter_date(created_at), tweet_dict))
            except:
                continue
        
        tweet_objects.sort(key=lambda x: x[0], reverse=True)
        
        # Get workspace root (go up 3 levels from script location)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
        output_dir = os.path.join(workspace_root, 'Dataset', 'Content', 'twitter-new')
        
        # Get path to waiting_collection.txt for pipeline integration
        codes_dir = os.path.dirname(script_dir)
        waiting_collection_file = os.path.join(codes_dir, 'pagelinks', 'waiting_collection.txt')
        
        # Check if folder exists, if not create it and write to CSV
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"{username}_{timestamp}.csv")
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Name', 'Handle', 'Timestamp', 'Verified', 'Content', 'Comments',
                            'Retweets', 'Likes', 'Analytics', 'Tags', 'Mentions', 'Emojis',
                            'Profile Image', 'Tweet Link', 'Tweet ID'])
            
            for _, tweet_dict in tweet_objects:
                # Format timestamp 
                created_at = tweet_dict.get('created_at', '')
                try:
                    dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
                    formatted_timestamp = dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                    date_str = dt.strftime("%Y-%m-%d")
                except:
                    formatted_timestamp = created_at
                    date_str = created_at.split('T')[0] if 'T' in created_at else created_at
                
                tweet_url = tweet_dict.get('tweet_url', '')
                
                writer.writerow([
                    user_name,
                    f"@{user_screen_name}",
                    formatted_timestamp,
                    user_verified,
                    tweet_dict.get('full_text', ''),
                    tweet_dict.get('reply_count', 0),
                    tweet_dict.get('retweet_count', 0),
                    tweet_dict.get('favorite_count', 0),
                    tweet_dict.get('views', {}).get('count', 0) if isinstance(tweet_dict.get('views'), dict) else 0,
                    str(tweet_dict.get('hashtags', [])),
                    str([f"@{m.get('screen_name', '')}" for m in tweet_dict.get('user_mentions', []) if isinstance(m, dict)]),
                    str(extract_emojis(tweet_dict.get('full_text', ''))),
                    tweet_dict.get('profile_image', user_profile_image),
                    tweet_url,
                    f"tweet_id:{tweet_dict.get('rest_id', '')}"
                ])
                
                # Write to waiting_collection.txt for pipeline integration
                # Format: timestamp\tsource\tdatetime\ttweet_url
                if tweet_url:
                    unique_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    with open(waiting_collection_file, 'a', encoding='utf-8') as f:
                        f.write(f"{unique_timestamp}\ttwitter_new\t{date_str}\t{tweet_url}\n")
        
        print(f"✓ Saved {len(tweet_objects)} tweets to {filename}")
        print(f"✓ Added {len(tweet_objects)} tweets to waiting_collection.txt for pipeline processing")


if __name__ == "__main__":
    main()