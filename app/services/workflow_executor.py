# services/workflow_executor.py

import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from ..config import config
from ..database import get_database
from ..services.tweet_fetcher import TweetFetcher
from ..services.media_handler import MediaHandler
from ..services.type_dispatcher import TypeDispatcher
from ..ai.openai.content_polisher import ContentPolisher
from ..schemas.workflow import WorkflowStep, WorkflowStepStatus, WorkflowResponse
from ..utils.logger import setup_logger
from ..utils.rate_limit_handler import RateLimitHandler
from ..enums.tweet_types import TweetTypes

logger = setup_logger(__name__)


class WorkflowExecutor:
    def __init__(self):
        self.workflows: Dict[str, WorkflowResponse] = {}
        
    async def execute_workflow(
        self,
        scrape_username: str,
        count: int = 1,
        tweet_type: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> WorkflowResponse:
        """Execute the complete workflow with timeout handling"""
        
        workflow_id = str(uuid.uuid4())
        return await self.execute_workflow_with_id(workflow_id, scrape_username, count, tweet_type, timeout)

    async def execute_workflow_with_id(
        self,
        workflow_id: str,
        scrape_username: str,
        count: int = 1,
        tweet_type: Optional[int] = None,
        timeout: Optional[int] = None
    ) -> WorkflowResponse:
        """Execute the complete workflow with a specific workflow ID"""
        
        step_timeout = timeout or config.workflow_step_timeout
        
        # Initialize workflow response
        workflow = WorkflowResponse(
            workflow_id=workflow_id,
            status=WorkflowStepStatus.PENDING,
            steps=[
                WorkflowStep(name="download_tweets"),
                WorkflowStep(name="process_and_classify"),
                WorkflowStep(name="polish_content"),
                WorkflowStep(name="post_tweets")
            ],
            summary={},
            created_at=datetime.now()
        )
        
        self.workflows[workflow_id] = workflow
        
        try:
            logger.info(f"Starting workflow {workflow_id} for @{scrape_username}")
            workflow.status = WorkflowStepStatus.RUNNING
            
            # Step 1: Download tweets from scrape account
            await self._execute_step_with_timeout(
                workflow, 0, "download_tweets",
                self._download_tweets_step, scrape_username, count, timeout=step_timeout
            )
            
            # Step 2: Process and classify tweets
            await self._execute_step_with_timeout(
                workflow, 1, "process_and_classify",
                self._process_and_classify_step, scrape_username, timeout=step_timeout
            )
            
            # Step 3: Polish content
            await self._execute_step_with_timeout(
                workflow, 2, "polish_content",
                self._polish_content_step, scrape_username, timeout=step_timeout
            )
            
            # Step 4: Post tweets to destination account (longer timeout for rate limits)
            posting_timeout = config.workflow_posting_timeout
            await self._execute_step_with_timeout(
                workflow, 3, "post_tweets",
                self._post_tweets_step, scrape_username, tweet_type, timeout=posting_timeout
            )
            
            # Update final status
            if all(step.status == WorkflowStepStatus.COMPLETED for step in workflow.steps):
                workflow.status = WorkflowStepStatus.COMPLETED
            else:
                workflow.status = WorkflowStepStatus.FAILED
                
            workflow.completed_at = datetime.now()
            if workflow.completed_at and workflow.created_at:
                workflow.total_duration = (workflow.completed_at - workflow.created_at).total_seconds()
                
            logger.info(f"Workflow {workflow_id} completed with status: {workflow.status}")
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {str(e)}")
            workflow.status = WorkflowStepStatus.FAILED
            workflow.completed_at = datetime.now()
            
        return workflow
    
    async def _execute_step_with_timeout(
        self,
        workflow: WorkflowResponse,
        step_index: int,
        step_name: str,
        step_func,
        *args,
        timeout: int
    ):
        """Execute a single step with timeout handling"""
        
        step = workflow.steps[step_index]
        step.status = WorkflowStepStatus.RUNNING
        step.start_time = datetime.now()
        
        try:
            logger.info(f"Executing step: {step_name}")
            
            # Execute step with timeout
            result = await asyncio.wait_for(
                step_func(*args),
                timeout=timeout
            )
            
            step.status = WorkflowStepStatus.COMPLETED
            step.result = result
            step.end_time = datetime.now()
            if step.start_time and step.end_time:
                step.duration = (step.end_time - step.start_time).total_seconds()
                
            logger.info(f"Step {step_name} completed successfully")
            
        except asyncio.TimeoutError:
            step.status = WorkflowStepStatus.TIMEOUT
            step.error = f"Step timed out after {timeout} seconds"
            step.end_time = datetime.now()
            if step.start_time and step.end_time:
                step.duration = (step.end_time - step.start_time).total_seconds()
            logger.error(f"Step {step_name} timed out")
            
        except Exception as e:
            step.status = WorkflowStepStatus.FAILED
            step.error = str(e)
            step.end_time = datetime.now()
            if step.start_time and step.end_time:
                step.duration = (step.end_time - step.start_time).total_seconds()
            logger.error(f"Step {step_name} failed: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {e}")
    
    async def _download_tweets_step(self, scrape_username: str, count: int) -> Dict[str, Any]:
        """Step 1: Download tweets from user"""
        try:
            from ..database.crud import TweetCRUD
            from ..schemas.tweet import TweetCreate
            
            db = next(get_database())
            crud = TweetCRUD(db)
            
            # Check if demo mode is enabled
            if config.workflow_demo_mode:
                logger.info("DEMO MODE: Using fake tweets for testing")
                
                # DEMO CONTENT: Create fake tweets with current time
                from datetime import datetime
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                demo_tweets_data = [
                    {
                        'tweet_id': f'demo_tweet_1_{int(datetime.now().timestamp())}',
                        'username': scrape_username,
                        'original_text': f'🚀 Demo tweet 1 from {current_time} - Testing workflow without rate limits!',
                        'polished_text': None,
                        'tweet_type': 1,
                        'media_urls': [],
                        'local_media_paths': []
                    },
                    {
                        'tweet_id': f'demo_tweet_2_{int(datetime.now().timestamp())}',
                        'username': scrape_username,
                        'original_text': f'📈 Demo tweet 2 from {current_time} - This is a promotional test tweet!',
                        'polished_text': None,
                        'tweet_type': 2,
                        'media_urls': [],
                        'local_media_paths': []
                    }
                ]
                
                saved_count = 0
                for tweet_data in demo_tweets_data:
                    if not crud.tweet_exists(tweet_data['tweet_id']):
                        tweet_create = TweetCreate(**tweet_data)
                        crud.create_tweet(tweet_create)
                        saved_count += 1
                
                return {
                    "downloaded_count": len(demo_tweets_data),
                    "saved_count": saved_count,
                    "scrape_username": scrape_username,
                    "message": "DEMO MODE - Using fake tweets for testing"
                }
            
            # REAL FETCHING: Get actual tweets from Twitter
            logger.info(f"Fetching real tweets from @{scrape_username}")
            
            fetcher = TweetFetcher()
            media_handler = MediaHandler()
            tweets_data = await fetcher.fetch_user_tweets(scrape_username, count)
            
            if not tweets_data:
                logger.warning(f"No tweets found for @{scrape_username}")
                return {
                    "downloaded_count": 0,
                    "saved_count": 0,
                    "scrape_username": scrape_username,
                    "message": f"No tweets found for @{scrape_username}"
                }
            
            saved_count = 0
            for tweet_data in tweets_data:
                if not crud.tweet_exists(tweet_data['tweet_id']):
                    tweet_create = TweetCreate(**tweet_data)
                    crud.create_tweet(tweet_create)
                    saved_count += 1
            
            logger.info(f"Successfully downloaded {saved_count} tweets from @{scrape_username}")
            
            return {
                "downloaded_count": len(tweets_data),
                "saved_count": saved_count,
                "scrape_username": scrape_username,
                "message": f"Downloaded {saved_count} tweets from @{scrape_username}"
            }
            
        except Exception as e:
            logger.error(f"Error in download_tweets_step: {str(e)}")
            raise
    
    async def _process_and_classify_step(self, scrape_username: str) -> Dict[str, Any]:
        """Step 2: Process and classify downloaded tweets"""
        try:
            from ..database.crud import TweetCRUD
            
            db = next(get_database())
            crud = TweetCRUD(db)
            
            # Get unprocessed tweets for the user
            tweets = crud.get_tweets_by_username(scrape_username, status="downloaded")
            
            if not tweets:
                return {"processed_count": 0, "message": "No tweets to process"}
            
            processed_count = 0
            for tweet in tweets:
                # Update status to processed
                crud.update_tweet(tweet.tweet_id, {"status": "processed"})
                processed_count += 1
            
            return {
                "processed_count": processed_count,
                "scrape_username": scrape_username
            }
            
        except Exception as e:
            logger.error(f"Error in process_and_classify_step: {str(e)}")
            raise
    
    async def _polish_content_step(self, scrape_username: str) -> Dict[str, Any]:
        """Step 3: Polish content with AI"""
        try:
            from ..database.crud import TweetCRUD
            
            db = next(get_database())
            crud = TweetCRUD(db)
            polisher = ContentPolisher()
            
            # Get unpolished tweets
            tweets = crud.get_tweets_by_username(scrape_username, status="processed")
            
            if not tweets:
                return {"polished_count": 0, "message": "No tweets to polish"}
            
            polished_count = 0
            for tweet in tweets:
                if not tweet.polished_text:
                    polished_text = await polisher.polish_tweet_text(
                        tweet.original_text,
                        tweet.tweet_type
                    )
                    
                    if polished_text:
                        crud.update_tweet(tweet.tweet_id, {
                            "polished_text": polished_text,
                            "status": "polished"
                        })
                        polished_count += 1
                    else:
                        # Use original text if polishing fails
                        crud.update_tweet(tweet.tweet_id, {
                            "polished_text": tweet.original_text,
                            "status": "polished"
                        })
                        polished_count += 1
            
            return {
                "polished_count": polished_count,
                "scrape_username": scrape_username
            }
            
        except Exception as e:
            logger.error(f"Error in polish_content_step: {str(e)}")
            raise
    
    async def _post_tweets_step(self, scrape_username: str, tweet_type: Optional[int] = None) -> Dict[str, Any]:
        """Step 4: Post the latest polished tweet to destination account - Using exact working code from test"""
        try:
            print(f"🔍 DEBUG: Starting post_tweets_step for @{scrape_username}")
            
            if not config.workflow_enable_auto_posting:
                print("❌ Auto posting is disabled in config")
                return {"posted_count": 0, "message": "Auto posting disabled"}
            
            print("✅ Auto posting is enabled")
            
            # Import required modules
            from ..database.crud import TweetCRUD
            from ..services.twitter_publisher import get_twitter_client
            from datetime import datetime
            import tweepy
            
            db = next(get_database())
            crud = TweetCRUD(db)
            
            # Get user tweets from scrape account
            tweets = crud.get_tweets_by_username(scrape_username, limit=50)
            print(f"🔍 DEBUG: Found {len(tweets)} total tweets in database")
            
            # Find latest polished tweet that hasn't been posted
            polished_tweets = [t for t in tweets if t.polished_text and t.status in ['polished', 'downloaded']]
            print(f"🔍 DEBUG: Found {len(polished_tweets)} polished tweets")
            
            if not polished_tweets:
                print("❌ No polished tweets found to post")
                return {"posted_count": 0, "message": "No polished tweets found to post"}
            
            latest_tweet = max(polished_tweets, key=lambda t: t.created_at)
            
            # Get text to post
            text_to_post = latest_tweet.polished_text or latest_tweet.original_text
            
            # Print what we're about to post (like test file)
            print("=" * 60)
            print("📝 ABOUT TO POST THIS TWEET:")
            print("=" * 60)
            print(f"Text: {text_to_post}")
            print(f"Length: {len(text_to_post)} characters")
            if latest_tweet.media_urls:
                print(f"Media: {len(latest_tweet.media_urls)} files")
            else:
                print("Media: None")
            print("=" * 60)
            
            # Create Twitter client (exact same as test file)
            client, api = get_twitter_client()
            
            # Post tweet using exact same logic as test file
            print("Posting tweet...")
            response = client.create_tweet(text=text_to_post)
            
            if response.data:
                tweet_id = response.data['id']
                print(f"✅ SUCCESS! Tweet posted with ID: {tweet_id}")
                
                # Update status
                crud.update_tweet(latest_tweet.tweet_id, {
                    "status": "published", 
                    "posted_at": datetime.now()
                })
                
                logger.info(f"Successfully posted tweet from @{scrape_username} to destination account as {tweet_id}")
                
                return {
                    "posted_count": 1,
                    "scrape_username": scrape_username,
                    "published_tweet_id": tweet_id,
                    "original_tweet_id": latest_tweet.tweet_id,
                    "message": f"Posted polished tweet from @{scrape_username} to destination account"
                }
            else:
                print("❌ No response data from Twitter API")
                raise Exception("No response data from Twitter API")
            
        except tweepy.Forbidden as e:
            print("❌ 403 FORBIDDEN ERROR - POSTING FAILED")
            print("=" * 60)
            print("🔍 POSSIBLE REASONS FOR 403 FORBIDDEN:")
            print("1. Account suspended or restricted")
            print("2. Duplicate content detected by X")
            print("3. Content violates X's policies")
            print("4. Account doesn't have posting permissions")
            print("5. Content too similar to recent posts")
            print("6. Automated posting detected")
            print("7. Account needs verification")
            print("8. Content contains banned keywords")
            print("=" * 60)
            print(f"Error details: {e}")
            raise Exception(f"403 Forbidden - You are not permitted to perform this action. Error: {e}")
            
        except tweepy.Unauthorized as e:
            print("❌ 401 UNAUTHORIZED ERROR - POSTING FAILED")
            print("=" * 60)
            print("🔍 POSSIBLE REASONS FOR 401 UNAUTHORIZED:")
            print("1. Invalid API credentials")
            print("2. API keys expired or revoked")
            print("3. Wrong access token")
            print("4. Account deleted or suspended")
            print("5. API permissions changed")
            print("=" * 60)
            print(f"Error details: {e}")
            raise Exception(f"401 Unauthorized - Check your API credentials. Error: {e}")
            
        except tweepy.TooManyRequests as e:
            print("❌ RATE LIMIT ERROR - POSTING FAILED")
            print("=" * 60)
            print("🔍 POSSIBLE REASONS FOR RATE LIMIT:")
            print("1. Too many posts in short time")
            print("2. X's rate limits exceeded")
            print("3. Account temporarily restricted")
            print("4. Need to wait before posting again")
            print("=" * 60)
            print(f"Error details: {e}")
            raise Exception("Rate limit exceeded while publishing tweet. Please try again later.")
            
        except tweepy.BadRequest as e:
            print("❌ BAD REQUEST ERROR - POSTING FAILED")
            print("=" * 60)
            print("🔍 POSSIBLE REASONS FOR BAD REQUEST:")
            print("1. Invalid tweet content")
            print("2. Invalid URLs in tweet")
            print("3. Character limit exceeded")
            print("4. Invalid media format")
            print("5. Content contains banned characters")
            print("=" * 60)
            print(f"Error details: {e}")
            raise Exception(f"Bad Request - Invalid tweet content. Error: {e}")
            
        except Exception as e:
            print("❌ UNEXPECTED ERROR - POSTING FAILED")
            print("=" * 60)
            print("🔍 POSSIBLE REASONS FOR UNEXPECTED ERROR:")
            print("1. Network connectivity issues")
            print("2. X API service down")
            print("3. Invalid tweet content")
            print("4. Media upload failed")
            print("5. Character limit exceeded")
            print("6. Invalid media format")
            print("=" * 60)
            print(f"Error type: {type(e)}")
            print(f"Error details: {e}")
            logger.error(f"Error in post_tweets_step: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            raise
    
    def get_workflow_status(self, workflow_id: str) -> Optional[WorkflowResponse]:
        """Get the status of a workflow"""
        return self.workflows.get(workflow_id)
    
    def cleanup_old_workflows(self, max_age_hours: int = 24):
        """Clean up old workflow records"""
        cutoff_time = datetime.now().replace(hour=datetime.now().hour - max_age_hours)
        
        workflows_to_remove = []
        for workflow_id, workflow in self.workflows.items():
            if workflow.created_at < cutoff_time:
                workflows_to_remove.append(workflow_id)
        
        for workflow_id in workflows_to_remove:
            del self.workflows[workflow_id]
            
        logger.info(f"Cleaned up {len(workflows_to_remove)} old workflows")


# Global workflow executor instance
workflow_executor = WorkflowExecutor() 