#!/usr/bin/env python3

import tweepy
import os
from dotenv import load_dotenv
from datetime import datetime

def test_post_with_detailed_logging():
    """Test posting with detailed logging and error explanations"""
    print("🧪 Testing Post with Detailed Logging")
    print("=" * 60)
    
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
        
        # Get your account info
        print("Getting account info...")
        me = client.get_me()
        if me.data:
            username = me.data.username
            print(f"✅ Account: @{username}")
        else:
            print("❌ Could not get account info")
            return
        
        # Create test tweet data (simulating your app's workflow)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        test_tweet_data = {
            'original_text': f"Original test tweet from {timestamp}",
            'polished_text': f"🚀 Enhanced test tweet from X Post Copier - {timestamp}\n\nThis demonstrates the new logging features with detailed error explanations!\n\n#XPostCopier #Test #Logging",
            'media_urls': []  # No media for this test
        }
        
        print("\n" + "=" * 60)
        print("📝 ABOUT TO POST THIS TWEET:")
        print("=" * 60)
        print(f"Text: {test_tweet_data['polished_text']}")
        print(f"Length: {len(test_tweet_data['polished_text'])} characters")
        print("Media: None")
        print("=" * 60)
        
        # Post the tweet
        print("Posting tweet...")
        response = client.create_tweet(text=test_tweet_data['polished_text'])
        
        if response.data:
            tweet_id = response.data['id']
            tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"
            
            print("\n" + "=" * 60)
            print("✅ SUCCESS! TWEET POSTED!")
            print("=" * 60)
            print(f"📝 Tweet ID: {tweet_id}")
            print(f"👤 Posted by: @{username}")
            print(f"🔗 Direct Link: {tweet_url}")
            print("=" * 60)
            
            # Clean up - delete the test tweet
            print("Cleaning up - deleting test tweet...")
            client.delete_tweet(tweet_id)
            print("✅ Test tweet deleted successfully")
            
            return True
            
        else:
            print("❌ No response data from Twitter API")
            return False
            
    except tweepy.Forbidden as e:
        print("❌ 403 FORBIDDEN ERROR - POSTING FAILED")
        print("=" * 60)
        print("🔍 POSSIBLE REASONS FOR 403 FORBIDDEN:")
        print("1. Account suspended or restricted")
        print("2. Duplicate content detected by X")
        print("3. Content violates X's policies")
        print("4. Account doesn't have posting permissions")
        print("5. Content too similar to recent posts")
        print("6. Automated posting detected")
        print("7. Account needs verification")
        print("8. Content contains banned keywords")
        print("=" * 60)
        print(f"Error details: {e}")
        return False
        
    except tweepy.Unauthorized as e:
        print("❌ 401 UNAUTHORIZED ERROR - POSTING FAILED")
        print("=" * 60)
        print("🔍 POSSIBLE REASONS FOR 401 UNAUTHORIZED:")
        print("1. Invalid API credentials")
        print("2. API keys expired or revoked")
        print("3. Wrong access token")
        print("4. Account deleted or suspended")
        print("5. API permissions changed")
        print("=" * 60)
        print(f"Error details: {e}")
        return False
        
    except tweepy.TooManyRequests as e:
        print("❌ RATE LIMIT ERROR - POSTING FAILED")
        print("=" * 60)
        print("🔍 POSSIBLE REASONS FOR RATE LIMIT:")
        print("1. Too many posts in short time")
        print("2. X's rate limits exceeded")
        print("3. Account temporarily restricted")
        print("4. Need to wait before posting again")
        print("=" * 60)
        print(f"Error details: {e}")
        return False
        
    except Exception as e:
        print("❌ UNEXPECTED ERROR - POSTING FAILED")
        print("=" * 60)
        print("🔍 POSSIBLE REASONS FOR UNEXPECTED ERROR:")
        print("1. Network connectivity issues")
        print("2. X API service down")
        print("3. Invalid tweet content")
        print("4. Media upload failed")
        print("5. Character limit exceeded")
        print("6. Invalid media format")
        print("=" * 60)
        print(f"Error type: {type(e)}")
        print(f"Error details: {e}")
        return False

if __name__ == "__main__":
    success = test_post_with_detailed_logging()
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n❌ Test failed - check the error details above") 