"""Request and response schemas for the Ops Digital Employee API."""

from typing import Optional

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="用户咨询或申告内容")
    user: str = Field(default="anonymous", min_length=1, description="报障人或提问人账号")
    contact: str = Field(default="", description="联系电话、邮箱或工号等联系方式")
    category: str = Field(default="general", description="问题类别")
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")


class RagSource(BaseModel):
    id: int
    question: str
    answer: str
    tags: list[str]
    score: float


class AskResponse(BaseModel):
    answer: str
    confidence: float
    fallback: bool
    ticket_id: Optional[int] = None
    sources: list[RagSource]


class RagStatusResponse(BaseModel):
    mode: str
    faq_count: int
    confidence_threshold: float
    direct_answer_threshold: float
    llm_provider: str
    vector_store: str
    scorer: str = "lexical"


class TicketCreate(BaseModel):
    question: str = Field(..., min_length=1)
    user: str = Field(..., min_length=1)
    contact: str = ""
    category: str = "general"
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")


class TicketUpdate(BaseModel):
    status: Optional[str] = Field(default=None, pattern="^(open|in_progress|resolved|closed)$")
    answer: Optional[str] = None
    resolver: Optional[str] = None
    contact: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = Field(default=None, pattern="^(low|normal|high|urgent)$")
    callback_status: Optional[str] = Field(default=None, pattern="^(pending|contacted|closed)$")
    callback_note: Optional[str] = None


class TicketResolve(BaseModel):
    resolution_note: str = Field(default="", description="内部处理记录，不写入知识库")
    resolver: str = Field(..., min_length=1)
    add_to_kb: bool = False
    kb_answer: str = Field(default="", description="沉淀到 FAQ 的答案，为空则不沉淀")
    callback_status: str = Field(default="contacted", pattern="^(pending|contacted|closed)$")
    callback_note: str = "已回访并告知处理结果"


class TicketResponse(BaseModel):
    id: int
    question: str
    user: str
    contact: str
    category: str
    priority: str
    status: str
    answer: Optional[str]
    resolver: Optional[str]
    callback_status: str
    callback_note: Optional[str]
    created_at: str
    updated_at: str
    resolved_at: Optional[str]


class UserCreate(BaseModel):
    username: str = Field(..., min_length=2)
    password: str = Field(..., min_length=4)
    role: str = Field(default="operator", pattern="^(admin|operator|viewer)$")
    full_name: str = ""
    department: str = ""
    phone: str = ""
    email: str = ""
    status: str = Field(default="active", pattern="^(active|frozen)$")


class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=2)
    password: Optional[str] = Field(default=None, min_length=4)
    role: Optional[str] = Field(default=None, pattern="^(admin|operator|viewer)$")
    full_name: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(active|frozen)$")


class UserStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|frozen)$")


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    full_name: str
    department: str
    phone: str
    email: str
    status: str
    created_at: str
    updated_at: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user: UserResponse


class FaqCreate(BaseModel):
    question: str = Field(..., min_length=3)
    answer: str = Field(..., min_length=3)
    tags: list[str] = Field(default_factory=list)


class FaqUpdate(BaseModel):
    question: Optional[str] = Field(default=None, min_length=3)
    answer: Optional[str] = Field(default=None, min_length=3)
    tags: Optional[list[str]] = None


class FaqResponse(BaseModel):
    id: int
    question: str
    answer: str
    tags: list[str]


class ResetPasswordRequest(BaseModel):
    username: str = Field(..., min_length=2)
    new_password: str = Field(..., min_length=4)
    requested_by: str = "system"


class CreateAccountRequest(BaseModel):
    username: str = Field(..., min_length=2)
    password: str = Field(..., min_length=4)
    role: str = Field(default="operator", pattern="^(admin|operator|viewer)$")
    full_name: str = ""
    department: str = ""
    phone: str = ""
    email: str = ""
    requested_by: str = "system"


class FreezeAccountRequest(BaseModel):
    username: str = Field(..., min_length=2)
    requested_by: str = "system"
    reason: str = "账号冻结清理"


class RpaJobResponse(BaseModel):
    job_id: int
    action: str
    status: str
    result: str
    steps: list[str]


class RpaCommandRequest(BaseModel):
    command: str = Field(..., min_length=2, description="自然语言指令，例如：重置ops01的密码为Temp1234")


class RpaCommandResponse(BaseModel):
    success: bool
    action: str
    message: str
    steps: list[str] | None = None
    status: str | None = None


class RpaJobHistoryItem(BaseModel):
    id: int
    action: str
    payload: str
    status: str
    result: str
    created_at: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="用户输入")


class ChatResponse(BaseModel):
    intent: str
    type: str
    content: str
    confidence: float | None = None
    ticket_id: int | None = None
    success: bool | None = None
    action: str | None = None
    steps: list[str] | None = None
    sources: list[dict] | None = None
