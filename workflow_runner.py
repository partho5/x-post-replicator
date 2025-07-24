#!/usr/bin/env python3
"""
Standalone workflow runner for cron/systemd execution
Usage: python workflow_runner.py [username] [count] [tweet_type]
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.workflow_executor import workflow_executor
from app.config import config
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


async def run_workflow(username: str = None, count: int = None, tweet_type: int = None):
    """Run the workflow with given parameters"""
    try:
        # Use provided username or default from config
        target_username = username or config.workflow_default_username
        if not target_username:
            logger.error("No username provided and no default username configured")
            return False
        
        # Use provided count or default from config
        target_count = count or config.workflow_default_count
        
        logger.info(f"Starting workflow for @{target_username}, count: {target_count}, type: {tweet_type}")
        
        # Execute workflow
        workflow = await workflow_executor.execute_workflow(
            username=target_username,
            count=target_count,
            tweet_type=tweet_type,
            timeout=config.workflow_step_timeout
        )
        
        # Log results
        logger.info(f"Workflow completed with status: {workflow.status}")
        
        # Log step results
        for step in workflow.steps:
            if step.status == "completed":
                logger.info(f"Step {step.name}: {step.result}")
            elif step.status in ["failed", "timeout"]:
                logger.error(f"Step {step.name}: {step.error}")
        
        return workflow.status == "completed"
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        return False


def main():
    """Main entry point for the script"""
    # Parse command line arguments
    username = None
    count = None
    tweet_type = None
    
    if len(sys.argv) > 1:
        username = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            count = int(sys.argv[2])
        except ValueError:
            logger.error("Count must be an integer")
            sys.exit(1)
    if len(sys.argv) > 3:
        try:
            tweet_type = int(sys.argv[3])
        except ValueError:
            logger.error("Tweet type must be an integer")
            sys.exit(1)
    
    # Run the workflow
    success = asyncio.run(run_workflow(username, count, tweet_type))
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 