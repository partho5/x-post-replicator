#!/usr/bin/env python3

import tweepy
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_write_access():
    """Test only Twitter API write access"""
    print("Testing Twitter API write access...")
    
    # Get credentials
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    
    try:
        # Test with v2 API (Client)
        print("Creating Twitter client...")
        client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        
        # Test posting a tweet directly
        print("Testing write access...")
        response = client.create_tweet(text="Test tweet from API - please ignore")
        
        if response.data is None:
            print("ERROR: No tweet data returned - write access failed")
            print(f"Response: {response}")
            return False
            
        print(f"SUCCESS: Write access works - Tweet ID: {response.data['id']}")
        
        # Delete the test tweet
        print("Cleaning up test tweet...")
        delete_response = client.delete_tweet(response.data['id'])
        print("SUCCESS: Test tweet deleted")
        
        return True
        
    except tweepy.TooManyRequests as e:
        print(f"ERROR: Rate limit error: {e}")
        return False
    except tweepy.Unauthorized as e:
        print(f"ERROR: Unauthorized error: {e}")
        return False
    except tweepy.Forbidden as e:
        print(f"ERROR: Forbidden error: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        print(f"Error type: {type(e)}")
        return False

if __name__ == "__main__":
    success = test_write_access()
    if success:
        print("\nSUCCESS: Twitter API write access successful!")
    else:
        print("\nFAILED: Twitter API write access failed!") 