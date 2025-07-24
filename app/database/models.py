# models.py

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class Tweet(Base):
    __tablename__ = "tweets"

    id = Column(Integer, primary_key=True, index=True)
    tweet_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, index=True, nullable=False)
    original_text = Column(Text, nullable=False)
    polished_text = Column(Text, nullable=True)
    tweet_type = Column(Integer, nullable=False)
    media_urls = Column(JSON, default=list)  # List of original media URLs
    local_media_paths = Column(JSON, default=list)  # List of local file paths
    status = Column(String, default="downloaded")  # downloaded, processed, posted, failed
    created_at = Column(DateTime, default=func.now())
    posted_at = Column(DateTime, nullable=True)