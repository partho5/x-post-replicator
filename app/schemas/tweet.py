# tweet.py


from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class TweetBase(BaseModel):
    tweet_id: str
    username: str
    original_text: str
    polished_text: Optional[str] = None
    tweet_type: int
    media_urls: List[str] = []


class TweetCreate(TweetBase):
    pass


class TweetUpdate(BaseModel):
    polished_text: Optional[str] = None
    status: Optional[str] = None
    posted_at: Optional[datetime] = None
    local_media_paths: Optional[List[str]] = None


class Tweet(TweetBase):
    id: int
    status: str
    local_media_paths: List[str] = []
    created_at: datetime
    posted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TweetDownloadRequest(BaseModel):
    username: str
    count: int = 10


class TweetPostRequest(BaseModel):
    tweet_type: int
    limit: Optional[int] = None