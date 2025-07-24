import tweepy
import requests
import tempfile
import os
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
    """Publish tweet to X and return published tweet ID"""
    try:
        client, api = get_twitter_client()

        # Get text to publish
        text = tweet_data.get('polished_text') or tweet_data['original_text']

        # Handle media if exists
        media_ids = []
        if tweet_data.get('media_urls'):
            media_ids = download_and_upload_media(tweet_data['media_urls'], api)

        # Post tweet
        response = client.create_tweet(
            text=text,
            media_ids=media_ids if media_ids else None
        )

        return response.data['id']
        
    except Exception as e:
        # Check if it's a rate limit error
        if RateLimitHandler.is_rate_limit_error(e):
            RateLimitHandler.log_rate_limit_error(e, "publishing tweet to X")
            raise Exception("Rate limit exceeded while publishing tweet. Please try again later.")
        else:
            raise