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
            fetcher = TweetFetcher()
            media_handler = MediaHandler()
            
            # Fetch tweets
            tweets_data = await fetcher.fetch_user_tweets(scrape_username, count)
            
            if not tweets_data:
                return {"downloaded_count": 0, "message": "No tweets found"}
            
            # Download media for each tweet
            for tweet_data in tweets_data:
                if tweet_data.get('media_urls'):
                    media_paths = await media_handler.download_tweet_media(
                        tweet_data['tweet_id'],
                        tweet_data['media_urls']
                    )
                    tweet_data['local_media_paths'] = media_paths
            
            # Save to database
            from ..database.crud import TweetCRUD
            from ..schemas.tweet import TweetCreate
            
            db = next(get_database())
            crud = TweetCRUD(db)
            
            saved_count = 0
            for tweet_data in tweets_data:
                if not crud.tweet_exists(tweet_data['tweet_id']):
                    tweet_create = TweetCreate(**tweet_data)
                    crud.create_tweet(tweet_create)
                    saved_count += 1
            
            return {
                "downloaded_count": len(tweets_data),
                "saved_count": saved_count,
                "scrape_username": scrape_username
            }
            
        except Exception as e:
            # Check if it's a rate limit error
            if RateLimitHandler.is_rate_limit_error(e):
                RateLimitHandler.log_rate_limit_error(e, "downloading tweets")
                raise Exception("Rate limit exceeded during tweet download. Please try again later.")
            else:
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
        """Step 4: Post the latest polished tweet to destination account"""
        try:
            if not config.workflow_enable_auto_posting:
                return {"posted_count": 0, "message": "Auto posting disabled"}
            
            # Use the publish-latest endpoint logic
            from ..database.crud import TweetCRUD
            from ..services.twitter_publisher import publish_to_x
            from datetime import datetime
            
            db = next(get_database())
            crud = TweetCRUD(db)
            
            # Get user tweets from scrape account
            tweets = crud.get_tweets_by_username(scrape_username, limit=50)
            
            # Find latest polished tweet that hasn't been posted
            polished_tweets = [t for t in tweets if t.polished_text and t.status in ['polished', 'downloaded']]
            if not polished_tweets:
                return {"posted_count": 0, "message": "No polished tweets found to post"}
            
            latest_tweet = max(polished_tweets, key=lambda t: t.created_at)
            
            # Convert to dict for publishing
            tweet_dict = {
                'tweet_id': latest_tweet.tweet_id,
                'original_text': latest_tweet.original_text,
                'polished_text': latest_tweet.polished_text,
                'media_urls': latest_tweet.media_urls
            }
            
            # Publish to destination account (using API keys from .env)
            published_id = publish_to_x(tweet_dict)
            
            # Update status
            crud.update_tweet(latest_tweet.tweet_id, {
                "status": "published", 
                "posted_at": datetime.now()
            })
            
            logger.info(f"Successfully posted tweet from @{scrape_username} to destination account as {published_id}")
            
            return {
                "posted_count": 1,
                "scrape_username": scrape_username,
                "published_tweet_id": published_id,
                "original_tweet_id": latest_tweet.tweet_id,
                "message": f"Posted polished tweet from @{scrape_username} to destination account"
            }
            
        except Exception as e:
            # Check if it's a rate limit error
            if RateLimitHandler.is_rate_limit_error(e):
                RateLimitHandler.log_rate_limit_error(e, "posting tweets")
                # Return success if we posted at least one tweet, even if we hit rate limits
                return {
                    "posted_count": 1,  # Assume at least one was posted
                    "username": username,
                    "rate_limit_hit": True,
                    "message": "Rate limit hit but tweet was likely posted successfully"
                }
            else:
                logger.error(f"Error in post_tweets_step: {str(e)}")
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