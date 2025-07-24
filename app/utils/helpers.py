# helpers.py

import os
import json
import aiofiles
from datetime import datetime
from typing import Any, Dict
from ..config import config


async def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        config.data_dir,
        config.raw_tweets_dir,
        config.media_dir,
        config.posted_dir
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)


async def save_json_data(data: Dict[Any, Any], filepath: str):
    """Save data as JSON file"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    async with aiofiles.open(filepath, 'w') as f:
        await f.write(json.dumps(data, indent=2, default=str))


async def load_json_data(filepath: str) -> Dict[Any, Any]:
    """Load data from JSON file"""
    if not os.path.exists(filepath):
        return {}

    async with aiofiles.open(filepath, 'r') as f:
        content = await f.read()
        return json.loads(content)


def get_timestamp() -> str:
    """Get current timestamp as string"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_tweet_media_dir(tweet_id: str) -> str:
    """Get media directory path for a tweet"""
    return os.path.join(config.media_dir, tweet_id)