#!/usr/bin/env python3
"""
Test script for the workflow functionality
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.workflow_executor import workflow_executor
from app.config import config


async def test_workflow():
    """Test the workflow execution"""
    print("Testing workflow execution...")
    
    # Check if default username is configured
    if not config.workflow_default_username:
        print("❌ No default username configured. Set WORKFLOW_DEFAULT_USERNAME in .env")
        return False
    
    print(f"✅ Using default username: @{config.workflow_default_username}")
    print(f"✅ Default count: {config.workflow_default_count}")
    print(f"✅ Step timeout: {config.workflow_step_timeout}s")
    print(f"✅ Auto posting: {config.workflow_enable_auto_posting}")
    
    try:
        # Execute workflow with test parameters
        workflow = await workflow_executor.execute_workflow(
            username=config.workflow_default_username,
            count=1,  # Test with just 1 tweet
            tweet_type=None,  # Test all types
            timeout=30  # Shorter timeout for testing
        )
        
        print(f"\n✅ Workflow completed with status: {workflow.status}")
        
        # Print step results
        for step in workflow.steps:
            print(f"  Step: {step.name}")
            print(f"    Status: {step.status}")
            print(f"    Duration: {step.duration:.2f}s")
            if step.error:
                print(f"    Error: {step.error}")
            if step.result:
                print(f"    Result: {step.result}")
            print()
        
        return workflow.status == "completed"
        
    except Exception as e:
        print(f"❌ Workflow test failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_workflow())
    sys.exit(0 if success else 1) 