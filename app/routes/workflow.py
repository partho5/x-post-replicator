# routes/workflow.py

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
from ..schemas.workflow import WorkflowRequest, WorkflowResponse, WorkflowStatusResponse
from ..services.workflow_executor import workflow_executor
from ..config import config
from ..utils.logger import setup_logger
from datetime import datetime

logger = setup_logger(__name__)
router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.post("/execute", response_model=WorkflowResponse)
async def execute_workflow(
    request: WorkflowRequest,
    background_tasks: BackgroundTasks
):
    """Execute the complete workflow asynchronously"""
    try:
        # Handle scrape username parameter
        scrape_username = request.scrape_x_username
        
        # Backward compatibility: if new param not provided, use legacy username
        if not scrape_username:
            scrape_username = request.username or config.workflow_default_username
        
        if not scrape_username:
            raise HTTPException(
                status_code=400,
                detail="Scrape username is required. Set WORKFLOW_DEFAULT_USERNAME in config or provide scrape_x_username in request."
            )
        
        # Use default count if not provided
        count = request.count or config.workflow_default_count
        
        # Generate workflow ID first
        import uuid
        workflow_id = str(uuid.uuid4())
        
        # Execute workflow in background
        background_tasks.add_task(
            workflow_executor.execute_workflow_with_id,
            workflow_id=workflow_id,
            scrape_username=scrape_username,
            count=count,
            tweet_type=request.tweet_type,
            timeout=request.timeout
        )
        
        # Return initial response with proper workflow ID
        return WorkflowResponse(
            workflow_id=workflow_id,
            status="running",
            steps=[],
            summary={
                "scrape_username": scrape_username,
                "count": count,
                "tweet_type": request.tweet_type,
                "message": "Workflow started in background"
            },
            created_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error starting workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute-sync", response_model=WorkflowResponse)
async def execute_workflow_sync(request: WorkflowRequest):
    """Execute the complete workflow synchronously and return results"""
    try:
        # Handle scrape username parameter
        scrape_username = request.scrape_x_username
        
        # Backward compatibility: if new param not provided, use legacy username
        if not scrape_username:
            scrape_username = request.username or config.workflow_default_username
        
        if not scrape_username:
            raise HTTPException(
                status_code=400,
                detail="Scrape username is required. Set WORKFLOW_DEFAULT_USERNAME in config or provide scrape_x_username in request."
            )
        
        # Use default count if not provided
        count = request.count or config.workflow_default_count
        
        # Execute workflow synchronously
        workflow = await workflow_executor.execute_workflow(
            scrape_username=scrape_username,
            count=count,
            tweet_type=request.tweet_type,
            timeout=request.timeout
        )
        
        return workflow
        
    except Exception as e:
        logger.error(f"Error executing workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str):
    """Get the status of a workflow"""
    try:
        workflow = workflow_executor.get_workflow_status(workflow_id)
        
        if not workflow:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow {workflow_id} not found"
            )
        
        # Calculate progress
        completed_steps = len([step for step in workflow.steps if step.status == "completed"])
        total_steps = len(workflow.steps)
        progress = completed_steps / total_steps if total_steps > 0 else 0.0
        
        # Find current step
        current_step = None
        for step in workflow.steps:
            if step.status == "running":
                current_step = step.name
                break
        
        return WorkflowStatusResponse(
            workflow_id=workflow.workflow_id,
            status=workflow.status,
            current_step=current_step,
            progress=progress,
            steps=workflow.steps,
            summary=workflow.summary,
            created_at=workflow.created_at,
            estimated_completion=None  # Could be calculated based on average step duration
        )
        
    except Exception as e:
        logger.error(f"Error getting workflow status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_workflows():
    """List all active workflows"""
    try:
        workflows = []
        for workflow_id, workflow in workflow_executor.workflows.items():
            workflows.append({
                "workflow_id": workflow_id,
                "status": workflow.status,
                "created_at": workflow.created_at,
                "completed_at": workflow.completed_at,
                "total_duration": workflow.total_duration
            })
        
        return {
            "workflows": workflows,
            "total_count": len(workflows)
        }
        
    except Exception as e:
        logger.error(f"Error listing workflows: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup")
async def cleanup_workflows():
    """Clean up old workflow records"""
    try:
        workflow_executor.cleanup_old_workflows()
        return {"message": "Workflow cleanup completed"}
        
    except Exception as e:
        logger.error(f"Error cleaning up workflows: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def workflow_health():
    """Health check for workflow system"""
    return {
        "status": "healthy",
        "active_workflows": len(workflow_executor.workflows),
        "default_username": config.workflow_default_username,
        "default_count": config.workflow_default_count,
        "step_timeout": config.workflow_step_timeout,
        "auto_posting_enabled": config.workflow_enable_auto_posting
    }


@router.get("/rate-limit-status")
async def get_rate_limit_status():
    """Get current rate limit status and information"""
    from ..utils.rate_limit_handler import RateLimitHandler
    
    return {
        "rate_limit_handler_available": True,
        "rate_limit_detection": {
            "tweepy_too_many_requests": "Supported",
            "http_429_errors": "Supported", 
            "retry_logic": "Available",
            "detailed_logging": "Enabled"
        },
        "recommendations": {
            "if_rate_limited": "Wait for retry-after time or reduce request frequency",
            "monitoring": "Check logs for 🚫 RATE LIMIT HIT messages",
            "best_practices": "Use reasonable delays between requests"
        }
    } 