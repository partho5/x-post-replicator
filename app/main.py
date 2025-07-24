# main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .routes import tweets, workflow
from .config import config
from .utils.logger import setup_logger
from .database import create_tables

logger = setup_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Twitter Automation API",
    description="A modular FastAPI application for Twitter automation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tweets.router)
app.include_router(workflow.router)

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting Twitter Automation API")
    create_tables()
    logger.info("Database tables created/verified")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Twitter Automation API",
        "version": "1.0.0",
        "endpoints": {
            "download_tweets": "POST /tweets/download",
            "post_by_type": "POST /tweets/post-by-type",
            "get_types": "GET /tweets/types",
            "get_user_tweets": "GET /tweets/user/{username}",
            "get_tweets_by_type": "GET /tweets/type/{tweet_type}",
            "get_tweet": "GET /tweets/{tweet_id}",
            "polish_tweet": "POST /tweets/{tweet_id}/polish",
            "publish_tweet": "POST /publish-latest/{username}"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
