# crud.py

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from . import models
from ..schemas import tweet as schemas


class TweetCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create_tweet(self, tweet: schemas.TweetCreate) -> models.Tweet:
        db_tweet = models.Tweet(**tweet.dict())
        self.db.add(db_tweet)
        self.db.commit()
        self.db.refresh(db_tweet)
        return db_tweet

    def get_tweet_by_tweet_id(self, tweet_id: str) -> Optional[models.Tweet]:
        return self.db.query(models.Tweet).filter(models.Tweet.tweet_id == tweet_id).first()

    def get_tweets_by_type(self, tweet_type: int, status: str = None, limit: int = None) -> List[models.Tweet]:
        query = self.db.query(models.Tweet).filter(models.Tweet.tweet_type == tweet_type)
        if status:
            query = query.filter(models.Tweet.status == status)
        if limit:
            query = query.limit(limit)
        return query.all()

    def get_tweets_by_username(self, username: str, limit: int = None) -> List[models.Tweet]:
        query = self.db.query(models.Tweet).filter(models.Tweet.username == username)

        # Apply order_by before limit
        query = query.order_by(models.Tweet.created_at.desc())

        if limit:
            query = query.limit(limit)

        return query.all()

    def update_tweet(self, tweet_id: str, updates) -> Optional[models.Tweet]:
        db_tweet = self.get_tweet_by_tweet_id(tweet_id)
        if db_tweet:
            # Handle both dictionary and schema objects
            if hasattr(updates, 'dict'):
                # It's a Pydantic schema object
                update_dict = updates.dict(exclude_unset=True)
            else:
                # It's a plain dictionary
                update_dict = updates
            
            for field, value in update_dict.items():
                setattr(db_tweet, field, value)
            self.db.commit()
            self.db.refresh(db_tweet)
        return db_tweet

    def tweet_exists(self, tweet_id: str) -> bool:
        return self.db.query(models.Tweet).filter(models.Tweet.tweet_id == tweet_id).first() is not None

    def get_unposted_tweets(self, tweet_type: int = None) -> List[models.Tweet]:
        query = self.db.query(models.Tweet).filter(
            and_(
                models.Tweet.status.in_(["downloaded", "processed"]),
                models.Tweet.posted_at.is_(None)
            )
        )
        if tweet_type:
            query = query.filter(models.Tweet.tweet_type == tweet_type)
        return query.all()

    def get_tweets_by_username(self, username: str, status: str = None, limit: int = None) -> List[models.Tweet]:
        """Get tweets by username with optional status filter"""
        query = self.db.query(models.Tweet).filter(models.Tweet.username == username)
        
        if status:
            query = query.filter(models.Tweet.status == status)
        
        # Apply order_by before limit
        query = query.order_by(models.Tweet.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()