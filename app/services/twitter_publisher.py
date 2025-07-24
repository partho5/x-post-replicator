# twitter_publisher.py

import tweepy
import requests
import tempfile
import os
import time
from typing import List, Optional
from ..config import config
from ..utils.rate_limit_handler import RateLimitHandler

# Twitter API setup
def get_twitter_client():
    client = tweepy.Client(
        bearer_token=config.twitter_bearer_token,
        consumer_key=config.twitter_api_key,
        consumer_secret=config.twitter_api_secret,
        access_token=config.twitter_access_token,
        access_token_secret=config.twitter_access_token_secret
    )

    auth = tweepy.OAuth1UserHandler(
        config.twitter_api_key,
        config.twitter_api_secret,
        config.twitter_access_token,
        config.twitter_access_token_secret
    )
    api = tweepy.API(auth)

    return client, api


def download_and_upload_media(media_urls: List[str], api) -> List[str]:
    """Download media from URLs and upload to Twitter"""
    media_ids = []

    for url in media_urls:
        try:
            # Download media
            response = requests.get(url)
            response.raise_for_status()

            # Save to temp file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            temp_file.write(response.content)
            temp_file.close()

            # Upload to Twitter
            media = api.media_upload(temp_file.name)
            media_ids.append(media.media_id)

            # Clean up temp file
            os.unlink(temp_file.name)

        except Exception as e:
            print(f"Failed to process media {url}: {e}")
            continue

    return media_ids


def publish_to_x(tweet_data: dict) -> str:
    """Publish tweet to X and return published tweet ID - Using simple, working approach"""
    try:
        client, api = get_twitter_client()

        # Get text to publish
        text = tweet_data.get('polished_text') or tweet_data['original_text']
        
        # Print what we're about to post
        print("=" * 60)
        print("📝 ABOUT TO POST THIS TWEET:")
        print("=" * 60)
        print(f"Text: {text}")
        print(f"Length: {len(text)} characters")
        if tweet_data.get('media_urls'):
            print(f"Media: {len(tweet_data['media_urls'])} files")
        else:
            print("Media: None")
        print("=" * 60)

        # Handle media if exists
        media_ids = []
        if tweet_data.get('media_urls'):
            media_ids = download_and_upload_media(tweet_data['media_urls'], api)

        # Post tweet using simple approach (like test_post_with_logging.py)
        print("Posting tweet...")
        if media_ids:
            response = client.create_tweet(text=text, media_ids=media_ids)
        else:
            response = client.create_tweet(text=text)

        if response.data:
            tweet_id = response.data['id']
            print(f"✅ SUCCESS! Tweet posted with ID: {tweet_id}")
            return tweet_id
        else:
            print("❌ No response data from Twitter API")
            raise Exception("No response data from Twitter API")
        
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
        raise Exception(f"403 Forbidden - You are not permitted to perform this action. Error: {e}")
        
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
        raise Exception(f"401 Unauthorized - Check your API credentials. Error: {e}")
        
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
        raise Exception("Rate limit exceeded while publishing tweet. Please try again later.")
        
    except tweepy.BadRequest as e:
        print("❌ BAD REQUEST ERROR - POSTING FAILED")
        print("=" * 60)
        print("🔍 POSSIBLE REASONS FOR BAD REQUEST:")
        print("1. Invalid tweet content")
        print("2. Invalid URLs in tweet")
        print("3. Character limit exceeded")
        print("4. Invalid media format")
        print("5. Content contains banned characters")
        print("=" * 60)
        print(f"Error details: {e}")
        raise Exception(f"Bad Request - Invalid tweet content. Error: {e}")
        
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
        raise