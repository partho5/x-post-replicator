#!/usr/bin/env python3

import tweepy
import os
from dotenv import load_dotenv

def test_environment_variables():
    """Test 1: Check if all environment variables are loaded correctly"""
    print("=== TEST 1: Environment Variables ===")
    
    # Load environment variables
    load_dotenv()
    
    # Check all required Twitter API variables
    env_vars = {
        "TWITTER_API_KEY": os.getenv("TWITTER_API_KEY"),
        "TWITTER_API_SECRET": os.getenv("TWITTER_API_SECRET"),
        "TWITTER_ACCESS_TOKEN": os.getenv("TWITTER_ACCESS_TOKEN"),
        "TWITTER_ACCESS_TOKEN_SECRET": os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
        "TWITTER_BEARER_TOKEN": os.getenv("TWITTER_BEARER_TOKEN"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY")
    }
    
    all_set = True
    for var_name, value in env_vars.items():
        if value:
            print(f"✅ {var_name}: {value[:10]}..." if len(value) > 10 else f"✅ {var_name}: {value}")
        else:
            print(f"❌ {var_name}: NOT SET")
            all_set = False
    
    if all_set:
        print("\n✅ All environment variables are loaded correctly!")
        return True
    else:
        print("\n❌ Some environment variables are missing!")
        return False

def test_post_sample_tweet():
    """Test 2: Post a sample tweet without scraping anything"""
    print("\n=== TEST 2: Post Sample Tweet ===")
    
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
        
        # Post a simple test tweet
        print("Posting sample tweet...")
        sample_text = "🧪 Test tweet from X Post Copier - Testing API functionality #test"
        
        response = client.create_tweet(text=sample_text)
        
        if response.data:
            tweet_id = response.data['id']
            print(f"✅ SUCCESS: Tweet posted successfully!")
            print(f"   Tweet ID: {tweet_id}")
            print(f"   Text: {sample_text}")
            
            # Clean up - delete the test tweet
            print("Cleaning up - deleting test tweet...")
            client.delete_tweet(tweet_id)
            print("✅ Test tweet deleted successfully")
            
            return True
        else:
            print("❌ ERROR: No response data from Twitter API")
            return False
            
    except tweepy.Forbidden as e:
        print(f"❌ 403 Forbidden error: {e}")
        print("This means your account doesn't have permission to post tweets")
        return False
    except tweepy.Unauthorized as e:
        print(f"❌ 401 Unauthorized error: {e}")
        print("This means your API credentials are invalid")
        return False
    except tweepy.TooManyRequests as e:
        print(f"❌ Rate limit error: {e}")
        print("You've hit Twitter's rate limits")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"Error type: {type(e)}")
        return False

def main():
    """Run both tests"""
    print("🧪 X Post Copier - Environment and Post Test")
    print("=" * 50)
    
    # Test 1: Environment variables
    env_success = test_environment_variables()
    
    # Test 2: Post sample tweet
    post_success = test_post_sample_tweet()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY:")
    print(f"Environment Variables: {'✅ PASS' if env_success else '❌ FAIL'}")
    print(f"Sample Tweet Post: {'✅ PASS' if post_success else '❌ FAIL'}")
    
    if env_success and post_success:
        print("\n🎉 ALL TESTS PASSED! Your setup is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main() 