# tweet_poster.py

import tweepy
from typing import List, Optional, Dict, Any
from ..config import config
from ..utils.logger import setup_logger
from ..services.media_handler import MediaHandler

logger = setup_logger(__name__)


class TweetPoster:
    def __init__(self):
        # Initialize Twitter API v1.1 for media upload
        auth = tweepy.OAuthHandler(
            config.twitter_api_key,
            config.twitter_api_secret
        )
        auth.set_access_token(
            config.twitter_access_token,
            config.twitter_access_token_secret
        )
        self.api_v1 = tweepy.API(auth, wait_on_rate_limit=True)

        # Initialize Twitter API v2 for posting tweets
        self.client = tweepy.Client(
            bearer_token=config.twitter_bearer_token,
            consumer_key=config.twitter_api_key,
            consumer_secret=config.twitter_api_secret,
            access_token=config.twitter_access_token,
            access_token_secret=config.twitter_access_token_secret,
            wait_on_rate_limit=True
        )

        self.media_handler = MediaHandler()

    async def post_tweet(self, text: str, media_paths: List[str] = None) -> Optional[Dict[str, Any]]:
        """Post a tweet with optional media attachments"""
        try:
            media_ids = []

            # Upload media if provided
            if media_paths:
                for media_path in media_paths:
                    media_id = await self._upload_media(media_path)
                    if media_id:
                        media_ids.append(media_id)

            # Post tweet
            if media_ids:
                response = self.client.create_tweet(text=text, media_ids=media_ids)
            else:
                response = self.client.create_tweet(text=text)

            if response.data:
                logger.info(f"Successfully posted tweet: {response.data['id']}")
                return {
                    'id': response.data['id'],
                    'text': text,
                    'media_count': len(media_ids)
                }
            else:
                logger.error("Failed to post tweet - no response data")
                return None

        except Exception as e:
            logger.error(f"Error posting tweet: {str(e)}")
            return None

    async def _upload_media(self, media_path: str) -> Optional[str]:
        """Upload media file and return media ID"""
        try:
            media = self.api_v1.media_upload(media_path)
            logger.info(f"Uploaded media: {media_path}")
            return media.media_id_string
        except Exception as e:
            logger.error(f"Error uploading media {media_path}: {str(e)}")
            return None

    def check_duplicate_content(self, text: str) -> bool:
        """Check if similar content was recently posted"""
        try:
            # Get recent tweets from authenticated user
            recent_tweets = self.client.get_users_tweets(
                id=self.client.get_me().data.id,
                max_results=10
            )

            if not recent_tweets.data:
                return False

            # Simple duplicate check - could be enhanced with fuzzy matching
            for tweet in recent_tweets.data:
                if text.lower() in tweet.text.lower() or tweet.text.lower() in text.lower():
                    logger.warning(f"Potential duplicate content detected")
                    return True

            return False

        except Exception as e:
            logger.error(f"Error checking duplicate content: {str(e)}")
            return False