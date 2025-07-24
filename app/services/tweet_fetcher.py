# tweet_fetcher.py

import tweepy
from typing import List, Dict, Any, Optional
from ..config import config
from ..utils.logger import setup_logger
from ..utils.rate_limit_handler import RateLimitHandler
from ..enums.tweet_types import TweetTypes

logger = setup_logger(__name__)


class TweetFetcher:
    def __init__(self):
        self.client = tweepy.Client(
            bearer_token=config.twitter_bearer_token,
            consumer_key=config.twitter_api_key,
            consumer_secret=config.twitter_api_secret,
            access_token=config.twitter_access_token,
            access_token_secret=config.twitter_access_token_secret,
            wait_on_rate_limit=True
        )

    async def fetch_user_tweets(self, username: str, count: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent tweets from a user"""
        try:
            logger.info(f"Fetching {count} tweets from @{username}")

            # Get user ID first
            user = self.client.get_user(username=username)
            if not user.data:
                raise ValueError(f"User @{username} not found")

            user_id = user.data.id

            # Fetch tweets with media information
            # Twitter API requires max_results to be between 5 and 100
            max_results = max(5, min(count, 100))
            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=max_results,
                tweet_fields=['created_at', 'attachments', 'public_metrics', 'context_annotations'],
                media_fields=['url', 'type', 'width', 'height'],
                expansions=['attachments.media_keys']
            )

            if not tweets.data:
                logger.warning(f"No tweets found for @{username}")
                return []

            # Process tweets and extract media
            processed_tweets = []
            media_dict = {}

            # Create media lookup dict
            if tweets.includes and 'media' in tweets.includes:
                media_dict = {media.media_key: media for media in tweets.includes['media']}

            for tweet in tweets.data:
                media_urls = []

                # Extract media URLs
                if tweet.attachments and 'media_keys' in tweet.attachments:
                    for media_key in tweet.attachments['media_keys']:
                        if media_key in media_dict:
                            media = media_dict[media_key]
                            if hasattr(media, 'url') and media.url:
                                media_urls.append(media.url)

                # Determine tweet type (simple heuristic)
                tweet_type = self._classify_tweet(tweet.text)

                processed_tweet = {
                    'tweet_id': str(tweet.id),  # Convert tweet.id to a string
                    'username': username,
                    'original_text': tweet.text,
                    'tweet_type': tweet_type,
                    'media_urls': media_urls,
                    'created_at': tweet.created_at
                }
                logger.debug(f"Processed tweet: {processed_tweet}")  # Log the processed tweet
                processed_tweets.append(processed_tweet)

            logger.info(f"Successfully fetched {len(processed_tweets)} tweets from @{username}")
            return processed_tweets

        except Exception as e:
            # Check if it's a rate limit error
            if RateLimitHandler.is_rate_limit_error(e):
                RateLimitHandler.log_rate_limit_error(e, f"fetching tweets from @{username}")
                raise Exception(f"Rate limit exceeded while fetching tweets from @{username}. Please try again later.")
            else:
                logger.error(f"Error fetching tweets from @{username}: {str(e)}")
                raise

    def _classify_tweet(self, text: str) -> int:
        """Simple tweet classification based on content"""
        text_lower = text.lower()

        if any(word in text_lower for word in ['buy', 'sale', 'discount', 'offer', 'promo']):
            return TweetTypes.PROMOTIONAL
        elif any(word in text_lower for word in ['news', 'breaking', 'announced', 'update']):
            return TweetTypes.NEWS
        elif text.startswith('RT @'):
            return TweetTypes.RETWEET
        elif len(text) > 200:  # Longer tweets might be part of a thread
            return TweetTypes.THREAD
        elif any(word in text_lower for word in ['i', 'me', 'my', 'personal']):
            return TweetTypes.PERSONAL
        else:
            return TweetTypes.GENERAL