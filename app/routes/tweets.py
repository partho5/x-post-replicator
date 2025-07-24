# routes/tweets.py
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from ..database import get_database, create_tables
from ..database.crud import TweetCRUD
from ..schemas.tweet import Tweet, TweetDownloadRequest, TweetPostRequest
from ..schemas.tweet import TweetUpdate
from ..services.tweet_fetcher import TweetFetcher
from ..services.media_handler import MediaHandler
from ..services.twitter_publisher import publish_to_x
from ..services.type_dispatcher import TypeDispatcher
from ..ai.openai.content_polisher import ContentPolisher
from ..utils.logger import setup_logger
from ..utils.helpers import ensure_directories
from ..enums.tweet_types import TweetTypes


logger = setup_logger(__name__)
router = APIRouter(prefix="/tweets", tags=["tweets"])

# Initialize database tables
create_tables()


@router.on_event("startup")
async def startup_event():
    """Initialize directories on startup"""
    await ensure_directories()


@router.post("/download", response_model=List[Tweet])
async def download_tweets(
        request: TweetDownloadRequest,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_database)
):
    """Download recent tweets from a user"""
    try:
        logger.info(f"Downloading {request.count} tweets from @{request.username}")

        fetcher = TweetFetcher()
        media_handler = MediaHandler()
        crud = TweetCRUD(db)

        # Fetch tweets
        tweets_data = await fetcher.fetch_user_tweets(request.username, request.count)

        if not tweets_data:
            raise HTTPException(status_code=404, detail="No tweets found")

        downloaded_tweets = []

        for tweet_data in tweets_data:
            # Skip if tweet already exists
            if crud.tweet_exists(tweet_data['tweet_id']):
                logger.info(f"Tweet {tweet_data['tweet_id']} already exists, skipping")
                continue

            # Download media in background
            if tweet_data['media_urls']:
                media_paths = await media_handler.download_tweet_media(
                    tweet_data['tweet_id'],
                    tweet_data['media_urls']
                )
                tweet_data['local_media_paths'] = media_paths

            # Create tweet record
            from ..schemas.tweet import TweetCreate
            tweet_create = TweetCreate(**tweet_data)
            db_tweet = crud.create_tweet(tweet_create)
            downloaded_tweets.append(db_tweet)

        logger.info(f"Downloaded {len(downloaded_tweets)} new tweets")
        return downloaded_tweets

    except Exception as e:
        logger.error(f"Error downloading tweets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/post-by-type")
async def post_tweets_by_type(
        request: TweetPostRequest,
        db: Session = Depends(get_database)
):
    """Post tweets of a specific type"""
    try:
        # Validate tweet type
        if request.tweet_type not in [t.value for t in TweetTypes]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid tweet type. Valid types: {[t.value for t in TweetTypes]}"
            )

        dispatcher = TypeDispatcher(db)
        results = await dispatcher.dispatch_tweets_by_type(
            request.tweet_type,
            request.limit
        )

        return {
            "tweet_type": request.tweet_type,
            "tweet_type_name": TweetTypes.get_name(request.tweet_type),
            "processed_count": len(results),
            "results": results
        }

    except Exception as e:
        logger.error(f"Error posting tweets by type: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
async def get_tweet_types():
    """Get available tweet types"""
    return {
        "tweet_types": [
            {"id": t.value, "name": TweetTypes.get_name(t.value)}
            for t in TweetTypes
        ]
    }


@router.get("/user/{username}", response_model=List[Tweet])
async def get_user_tweets(
        username: str,
        limit: int = 10,
        db: Session = Depends(get_database)
):
    """Get stored tweets for a user"""
    crud = TweetCRUD(db)
    tweets = crud.get_tweets_by_username(username, limit)
    return tweets


@router.get("/type/{tweet_type}", response_model=List[Tweet])
async def get_tweets_by_type(
        tweet_type: int,
        status: str = None,
        limit: int = None,
        db: Session = Depends(get_database)
):
    """Get tweets by type and optional status"""
    if tweet_type not in [t.value for t in TweetTypes]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tweet type. Valid types: {[t.value for t in TweetTypes]}"
        )

    crud = TweetCRUD(db)
    tweets = crud.get_tweets_by_type(tweet_type, status, limit)
    return tweets


@router.get("/{tweet_id}", response_model=Tweet)
async def get_tweet(tweet_id: str, db: Session = Depends(get_database)):
    """Get a specific tweet"""
    crud = TweetCRUD(db)
    tweet = crud.get_tweet_by_tweet_id(tweet_id)

    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    return tweet


@router.post("/{tweet_id}/polish")
async def polish_tweet(tweet_id: str, db: Session = Depends(get_database)):
    """Polish a specific tweet's content"""
    try:
        crud = TweetCRUD(db)
        tweet = crud.get_tweet_by_tweet_id(tweet_id)

        if not tweet:
            raise HTTPException(status_code=404, detail="Tweet not found")

        if tweet.polished_text:
            return {"message": "Tweet already polished", "polished_text": tweet.polished_text}

        polisher = ContentPolisher()
        polished_text = await polisher.polish_tweet_text(
            tweet.original_text,
            tweet.tweet_type
        )

        if polished_text:
            # crud.update_tweet(tweet_id, {"polished_text": polished_text, "status": "processed"})
            update_data = TweetUpdate(polished_text=polished_text, status="processed")
            crud.update_tweet(tweet_id, update_data)
            return {"message": "Tweet polished successfully", "polished_text": polished_text}
        else:
            raise HTTPException(status_code=500, detail="Failed to polish tweet")

    except Exception as e:
        logger.error(f"Error polishing tweet: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/publish-latest/{username}")
async def publish_latest_tweet(username: str, db: Session = Depends(get_database)):
    print("publish_latest_tweet()")
    """Find latest downloaded tweet and publish it"""
    crud = TweetCRUD(db)

    # Get user tweets
    tweets = crud.get_tweets_by_username(username, limit=50)

    # Find latest downloaded tweet
    downloaded_tweets = [t for t in tweets if t.status == 'downloaded']
    if not downloaded_tweets:
        raise HTTPException(status_code=404, detail="No downloaded tweets found")

    latest_tweet = max(downloaded_tweets, key=lambda t: t.created_at)

    try:
        # Convert SQLAlchemy model to dict properly
        tweet_dict = {
            'tweet_id': latest_tweet.tweet_id,
            'original_text': latest_tweet.original_text,
            'polished_text': latest_tweet.polished_text,
            'media_urls': latest_tweet.media_urls
        }

        # Publish to X
        published_id = publish_to_x(tweet_dict)

        # Update status
        update_data = TweetUpdate(status="published", posted_at=datetime.now())
        crud.update_tweet(latest_tweet.tweet_id, update_data)

        return {
            "success": True,
            "tweet_id": latest_tweet.tweet_id,
            "published_id": published_id
        }

    except Exception as e:
        # Update status to failed
        update_data = TweetUpdate(status="failed")
        crud.update_tweet(latest_tweet.tweet_id, update_data)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/publish/{tweet_id}")
async def publish_tweet(tweet_id: str, db: Session = Depends(get_database)):
    """Publish specific tweet by ID"""
    crud = TweetCRUD(db)

    # Get tweet - use correct method
    tweet = crud.get_tweet_by_tweet_id(tweet_id)
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")

    if tweet.status == "published":
        raise HTTPException(status_code=400, detail="Tweet already published")

    try:
        # Convert SQLAlchemy model to dict properly
        tweet_dict = {
            'tweet_id': tweet.tweet_id,
            'original_text': tweet.original_text,
            'polished_text': tweet.polished_text,
            'media_urls': tweet.media_urls
        }

        # Publish to X
        published_id = publish_to_x(tweet_dict)

        # Update status
        update_data = TweetUpdate(status="published", posted_at=datetime.now())
        crud.update_tweet(tweet_id, update_data)

        return {
            "success": True,
            "tweet_id": tweet_id,
            "published_id": published_id
        }

    except Exception as e:
        # Update status to failed
        update_data = TweetUpdate(status="failed")
        crud.update_tweet(tweet_id, update_data)
        raise HTTPException(status_code=500, detail=str(e))