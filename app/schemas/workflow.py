# schemas/workflow.py

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class WorkflowStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class WorkflowStep(BaseModel):
    name: str
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class WorkflowRequest(BaseModel):
    scrape_x_username: Optional[str] = Field(None, description="Username to scrape tweets from")
    count: int = Field(default=1, ge=1, le=100, description="Number of tweets to process")
    tweet_type: Optional[int] = Field(None, description="Specific tweet type to post (1-6)")
    timeout: Optional[int] = Field(None, ge=10, le=300, description="Timeout per step in seconds")
    
    # Backward compatibility
    username: Optional[str] = Field(None, description="Legacy: username for both scraping and posting")


class WorkflowResponse(BaseModel):
    workflow_id: str
    status: WorkflowStepStatus
    steps: List[WorkflowStep]
    total_duration: Optional[float] = None
    summary: Dict[str, Any]
    created_at: datetime
    completed_at: Optional[datetime] = None


class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    status: WorkflowStepStatus
    current_step: Optional[str] = None
    progress: float = Field(0.0, ge=0.0, le=1.0)
    steps: List[WorkflowStep]
    summary: Dict[str, Any]
    created_at: datetime
    estimated_completion: Optional[datetime] = None 