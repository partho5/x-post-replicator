# config.py

import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from typing import ClassVar


load_dotenv()


class Settings(BaseSettings):
    # Twitter API
    twitter_api_key: str = os.getenv("TWITTER_API_KEY", "")
    twitter_api_secret: str = os.getenv("TWITTER_API_SECRET", "")
    twitter_access_token: str = os.getenv("TWITTER_ACCESS_TOKEN", "")
    twitter_access_token_secret: str = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
    twitter_bearer_token: str = os.getenv("TWITTER_BEARER_TOKEN", "")

    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: ClassVar[str] = 'gpt-4.1-mini'
    OPENAI_TEMPERATURE: ClassVar[float] = 0.7
    OPENAI_MAX_TOKENS: ClassVar[int] = 500

    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/tweets.db")

    # App Settings
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    max_tweets_per_request: int = int(os.getenv("MAX_TWEETS_PER_REQUEST", "10"))
    media_download_timeout: int = int(os.getenv("MEDIA_DOWNLOAD_TIMEOUT", "30"))

    # Workflow Settings
    workflow_default_username: str = os.getenv("WORKFLOW_DEFAULT_USERNAME", "")
    workflow_default_count: int = int(os.getenv("WORKFLOW_DEFAULT_COUNT", "1"))
    workflow_step_timeout: int = int(os.getenv("WORKFLOW_STEP_TIMEOUT", "60"))
    workflow_posting_timeout: int = int(os.getenv("WORKFLOW_POSTING_TIMEOUT", "1200"))  # 20 minutes for posting
    workflow_enable_auto_posting: bool = os.getenv("WORKFLOW_ENABLE_AUTO_POSTING", "true").lower() == "true"

    # Directories
    data_dir: str = "./data"
    raw_tweets_dir: str = "./data/raw_tweets"
    media_dir: str = "./data/media"
    posted_dir: str = "./data/posted"

    class Config:
        env_file = ".env"


config = Settings()