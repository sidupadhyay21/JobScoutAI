"""
Shared data models for DynamoDB tables
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    FOUND = "found"
    KIT_GENERATED = "kit_generated"
    FORM_FILLED = "form_filled"
    READY_TO_SUBMIT = "ready_to_submit"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(BaseModel):
    """Job posting model"""
    job_id: str
    user_id: str = "demo_user"
    title: str
    company: str
    location: Optional[str] = None
    description: str
    url: str
    source: str  # e.g., "LinkedIn", "Indeed"
    status: JobStatus = JobStatus.FOUND
    created_at: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    updated_at: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    metadata: Optional[Dict[str, Any]] = None

    def to_dynamodb(self) -> Dict[str, Any]:
        """Convert to DynamoDB item format"""
        return {
            "job_id": self.job_id,
            "user_id": self.user_id,
            "title": self.title,
            "company": self.company,
            "location": self.location or "",
            "description": self.description,
            "url": self.url,
            "source": self.source,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata or {}
        }


class ApplicationKit(BaseModel):
    """Generated application kit model"""
    kit_id: str
    job_id: str
    user_id: str = "demo_user"
    cover_letter: str
    resume_bullets: List[str]
    cover_letter_s3_key: Optional[str] = None
    created_at: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    metadata: Optional[Dict[str, Any]] = None

    def to_dynamodb(self) -> Dict[str, Any]:
        """Convert to DynamoDB item format"""
        return {
            "kit_id": self.kit_id,
            "job_id": self.job_id,
            "user_id": self.user_id,
            "cover_letter": self.cover_letter,
            "resume_bullets": self.resume_bullets,
            "cover_letter_s3_key": self.cover_letter_s3_key or "",
            "created_at": self.created_at,
            "metadata": self.metadata or {}
        }


class FormFillTask(BaseModel):
    """Form filling task model"""
    task_id: str
    job_id: str
    user_id: str = "demo_user"
    application_url: str
    status: TaskStatus = TaskStatus.PENDING
    screenshot_s3_keys: List[str] = Field(default_factory=list)
    filled_fields: Dict[str, str] = Field(default_factory=dict)
    error_message: Optional[str] = None
    created_at: int = Field(default_factory=lambda: int(datetime.now().timestamp()))
    completed_at: Optional[int] = None

    def to_dynamodb(self) -> Dict[str, Any]:
        """Convert to DynamoDB item format"""
        return {
            "task_id": self.task_id,
            "job_id": self.job_id,
            "user_id": self.user_id,
            "application_url": self.application_url,
            "status": self.status.value,
            "screenshot_s3_keys": self.screenshot_s3_keys,
            "filled_fields": self.filled_fields,
            "error_message": self.error_message or "",
            "created_at": self.created_at,
            "completed_at": self.completed_at or 0
        }
