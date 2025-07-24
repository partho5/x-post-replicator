#!/usr/bin/env python3

import tweepy
import os
from dotenv import load_dotenv
from datetime import datetime

def post_tweet_with_link():
    """Post a tweet and provide the direct link"""
    print("=== POSTING TWEET WITH LINK ===")
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Get credentials
        api_key = os.getenv("TWITTER_API_KEY")
        api_secret = os.getenv("TWITTER_API_SECRET")
        access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        
        print("Creating Twitter client...")
        client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        
        # Get your own user info to get your username
        print("Getting your account info...")
        me = client.get_me()
        if me.data:
            username = me.data.username
            print(f"✅ Found your account: @{username}")
        else:
            print("❌ Could not get your account info")
            return
        
        # Post a tweet with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tweet_text = f"🚀 X Post Copier Test - {timestamp}\n\nThis is a test tweet from the X Post Copier application!\n\n#XPostCopier #Test"
        
        print(f"Posting tweet: {tweet_text}")
        response = client.create_tweet(text=tweet_text)
        
        if response.data:
            tweet_id = response.data['id']
            tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"
            
            print("\n" + "="*60)
            print("✅ TWEET POSTED SUCCESSFULLY!")
            print("="*60)
            print(f"📝 Tweet ID: {tweet_id}")
            print(f"👤 Posted by: @{username}")
            print(f"🔗 Direct Link: {tweet_url}")
            print(f"📅 Time: {timestamp}")
            print("="*60)
            
            print(f"\n🌐 You can view your tweet at: {tweet_url}")
            print("📱 Check your X profile to see the tweet!")
            
            return tweet_id, tweet_url
            
        else:
            print("❌ ERROR: No response data from Twitter API")
            return None, None
            
    except tweepy.Forbidden as e:
        print(f"❌ 403 Forbidden error: {e}")
        print("This means your account doesn't have permission to post tweets")
        return None, None
    except tweepy.Unauthorized as e:
        print(f"❌ 401 Unauthorized error: {e}")
        print("This means your API credentials are invalid")
        return None, None
    except tweepy.TooManyRequests as e:
        print(f"❌ Rate limit error: {e}")
        print("You've hit Twitter's rate limits")
        return None, None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"Error type: {type(e)}")
        return None, None

def main():
    """Post tweet and show link"""
    print("🚀 X Post Copier - Post Tweet with Link")
    print("="*60)
    
    tweet_id, tweet_url = post_tweet_with_link()
    
    if tweet_id and tweet_url:
        print(f"\n🎉 SUCCESS! Your tweet is now live on X!")
        print(f"🔗 View it here: {tweet_url}")
        print("\n💡 Note: The tweet will remain on your profile unless you delete it manually.")
    else:
        print("\n❌ Failed to post tweet. Check the errors above.")

if __name__ == "__main__":
    main() 