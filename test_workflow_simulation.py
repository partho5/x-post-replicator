#!/usr/bin/env python3

import tweepy
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_workflow_simulation():
    """Simulate the exact workflow to find the 403 error"""
    print("Testing workflow simulation...")
    
    # Get credentials
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    
    try:
        # Create client (same as in your app)
        print("1. Creating Twitter client...")
        client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        
        # Test 1: Read tweets (like tweet_fetcher.py)
        print("2. Testing tweet reading (like tweet_fetcher.py)...")
        try:
            user = client.get_user(username="jack98tom")
            if user.data:
                print(f"   SUCCESS: Read access works - Found user: {user.data.name}")
            else:
                print("   WARNING: No user data returned")
        except Exception as e:
            print(f"   ERROR reading tweets: {e}")
        
        # Wait a bit to avoid rate limits
        time.sleep(2)
        
        # Test 2: Post tweet (like twitter_publisher.py)
        print("3. Testing tweet posting (like twitter_publisher.py)...")
        try:
            response = client.create_tweet(text="Workflow simulation test - please ignore")
            if response.data:
                print(f"   SUCCESS: Write access works - Tweet ID: {response.data['id']}")
                
                # Clean up
                print("   Cleaning up test tweet...")
                client.delete_tweet(response.data['id'])
                print("   SUCCESS: Test tweet deleted")
            else:
                print("   ERROR: No tweet data returned")
        except Exception as e:
            print(f"   ERROR posting tweet: {e}")
            print(f"   Error type: {type(e)}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_workflow_simulation()
    if success:
        print("\nSUCCESS: Workflow simulation completed!")
    else:
        print("\nFAILED: Workflow simulation failed!") 