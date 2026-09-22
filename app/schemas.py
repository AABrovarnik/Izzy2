from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(default="", max_length=10000)
    priority: Literal["low", "normal", "high", "urgent"] = "normal"
    due_at: datetime | None = None
    timezone: str = "UTC"
    source_id: str | None = None


class TaskRead(TaskCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    version: int
    created_at: datetime
    completed_at: datetime | None = None


class ProposalCreate(BaseModel):
    action_type: Literal[
        "CREATE_EVENT",
        "UPDATE_EVENT",
        "DELETE_EVENT",
        "SEND_EMAIL",
        "DRAFT_EMAIL",
        "CREATE_TASK",
    ]
    payload: dict[str, Any] = Field(default_factory=dict)
    preview: str = Field(min_length=1, max_length=700)
    confidence: float = Field(ge=0, le=1)
    risk: Literal["low", "medium", "high"] = "medium"
    source_id: str | None = None
    task_id: str | None = None
    idempotency_key: str = Field(min_length=8, max_length=255)


class ProposalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    action_type: str
    payload: dict[str, Any]
    preview: str
    status: str
    confidence: float
    risk: str
    version: int
    expires_at: datetime
    created_at: datetime
    approved_at: datetime | None = None
    executed_at: datetime | None = None


class ApprovalBody(BaseModel):
    version: int = Field(ge=1)
    approval_token: str = Field(min_length=20)


class TelegramUpdate(BaseModel):
    update_id: int
    message: dict[str, Any] | None = None


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_type: str
    external_id: str
    subject: str | None
    content: str
    occurred_at: datetime | None
    created_at: datetime
