from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class AgentMailMessageSummary(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    inbox_id: str
    message_id: str
    thread_id: Optional[str] = None
    labels: list[str] = Field(default_factory=list)
    timestamp: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    from_address: Optional[str] = Field(default=None, alias="from")
    to: list[str] = Field(default_factory=list)
    cc: list[str] = Field(default_factory=list)
    bcc: list[str] = Field(default_factory=list)
    subject: Optional[str] = None
    preview: Optional[str] = None
    size: Optional[int] = None


class AgentMailMessageDetail(AgentMailMessageSummary):
    text: Optional[str] = None
    html: Optional[str] = None
    extracted_text: Optional[str] = None
    extracted_html: Optional[str] = None
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class AgentMailMessageList(BaseModel):
    count: int
    messages: list[AgentMailMessageSummary]
    next_page_token: Optional[str] = None


class AgentMailMockSendResponse(BaseModel):
    run_id: str
    delivery_status: str
    message_id: Optional[str] = None
    thread_id: Optional[str] = None
    error: Optional[str] = None
