# type_dispatcher.py

from typing import List, Optional
from sqlalchemy.orm import Session
from ..database.crud import TweetCRUD
from ..database.models import Tweet
from ..services.tweet_poster import TweetPoster
from ..ai.openai.content_polisher import ContentPolisher
from ..utils.logger import setup_logger
from ..utils.helpers import save_json_data, get_timestamp
from ..config import config
from ..enums.tweet_types import TweetTypes
from datetime import datetime
import os

logger = setup_logger(__name__)


class TypeDispatcher:
    def __init__(self, db: Session):
        self.db = db
        self.crud = TweetCRUD(db)
        self.poster = TweetPoster()
        self.polisher = ContentPolisher()

    async def dispatch_tweets_by_type(self, tweet_type: int, limit: Optional[int] = None) -> List[dict]:
        """Process and post tweets of a specific type"""
        try:
            logger.info(f"Dispatching tweets of type {TweetTypes.get_name(tweet_type)}")

            # Get unposted tweets of the specified type
            tweets = self.crud.get_unposted_tweets(tweet_type)

            if limit:
                tweets = tweets[:limit]

            if not tweets:
                logger.info(f"No unposted tweets found for type {tweet_type}")
                return []

            results = []

            for tweet in tweets:
                try:
                    result = await self._process_single_tweet(tweet)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error processing tweet {tweet.tweet_id}: {str(e)}")
                    # Update tweet status to failed
                    self.crud.update_tweet(tweet.tweet_id, {"status": "failed"})
                    results.append({
                        "tweet_id": tweet.tweet_id,
                        "status": "failed",
                        "error": str(e)
                    })

            logger.info(f"Processed {len(results)} tweets of type {tweet_type}")
            return results

        except Exception as e:
            logger.error(f"Error dispatching tweets by type {tweet_type}: {str(e)}")
            raise

    async def _process_single_tweet(self, tweet: Tweet) -> dict:
        """Process and post a single tweet"""
        logger.info(f"Processing tweet {tweet.tweet_id}")

        # Polish the content if not already done
        if not tweet.polished_text:
            polished_text = await self.polisher.polish_tweet_text(
                tweet.original_text,
                tweet.tweet_type
            )

            if polished_text:
                self.crud.update_tweet(tweet.tweet_id, {"polished_text": polished_text})
                tweet.polished_text = polished_text
            else:
                # Use original text if polishing fails
                tweet.polished_text = tweet.original_text

        # Check for duplicate content
        if self.poster.check_duplicate_content(tweet.polished_text):
            logger.warning(f"Skipping tweet {tweet.tweet_id} - duplicate content detected")
            self.crud.update_tweet(tweet.tweet_id, {"status": "skipped"})
            return {
                "tweet_id": tweet.tweet_id,
                "status": "skipped",
                "reason": "duplicate_content"
            }

        # Post the tweet
        post_result = await self.poster.post_tweet(
            tweet.polished_text,
            tweet.local_media_paths
        )

        if post_result:
            # Update tweet status
            try:
                self.crud.update_tweet(tweet.tweet_id, {
                    "status": "posted",
                    "posted_at": datetime.now()
                })
                logger.info(f"Successfully updated tweet {tweet.tweet_id} status to posted")
            except Exception as update_error:
                logger.error(f"Error updating tweet {tweet.tweet_id} status: {str(update_error)}")
                # Continue anyway since the tweet was posted successfully

            # Save posted tweet data
            await self._save_posted_tweet_data(tweet, post_result)

            logger.info(f"Successfully posted tweet {tweet.tweet_id}")
            return {
                "tweet_id": tweet.tweet_id,
                "status": "posted",
                "posted_tweet_id": post_result['id']
            }
        else:
            self.crud.update_tweet(tweet.tweet_id, {"status": "failed"})
            return {
                "tweet_id": tweet.tweet_id,
                "status": "failed",
                "reason": "post_failed"
            }

    async def _save_posted_tweet_data(self, tweet: Tweet, post_result: dict):
        """Save posted tweet data to JSON file"""
        try:
            posted_data = {
                "original_tweet_id": tweet.tweet_id,
                "posted_tweet_id": post_result['id'],
                "username": tweet.username,
                "original_text": tweet.original_text,
                "polished_text": tweet.polished_text,
                "tweet_type": tweet.tweet_type,
                "tweet_type_name": TweetTypes.get_name(tweet.tweet_type),
                "media_count": post_result.get('media_count', 0),
                "posted_at": datetime.now().isoformat(),
                "local_media_paths": tweet.local_media_paths
            }

            filepath = os.path.join(config.posted_dir, f"{tweet.tweet_id}.json")
            await save_json_data(posted_data, filepath)

        except Exception as e:
            logger.error(f"Error saving posted tweet data: {str(e)}")