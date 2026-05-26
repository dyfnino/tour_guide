from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class AiTestBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: Optional[str] = None
    difficulty: Optional[str] = None
    duration: Optional[int] = None

class AiTestCreate(AiTestBase):
    pass

class AiTestUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    difficulty: Optional[str] = None
    duration: Optional[int] = None

class AiTestInDB(AiTestBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

class AiTest(AiTestInDB):
    class Config:
        from_attributes = True

class TestResultBase(BaseModel):
    user_id: int
    test_id: int
    score: int
    result: Optional[str] = None
    feedback: Optional[str] = None

class TestResultCreate(TestResultBase):
    pass

class TestResultInDB(TestResultBase):
    id: int
    created_at: datetime

class TestResult(TestResultInDB):
    class Config:
        from_attributes = True


# ---- AI 对话 / 测评请求 ----

class ChatHistoryItem(BaseModel):
    role: str        # user | assistant | system
    content: str


class ChatRequest(BaseModel):
    message: Optional[str] = None
    history: Optional[List[ChatHistoryItem]] = None
    image_urls: Optional[List[str]] = None
    audio_urls: Optional[List[str]] = None
    image_paths: Optional[List[str]] = None
    audio_paths: Optional[List[str]] = None


class ChatResponse(BaseModel):
    text: str
    model: str
    mock: bool
    usage: Optional[Dict[str, Any]] = None


class EvaluationRequest(BaseModel):
    test_id: Optional[int] = None
    test_type: str            # theory / lecture / interview
    topic: Optional[str] = None
    user_answer: Optional[str] = None
    image_urls: Optional[List[str]] = None
    audio_urls: Optional[List[str]] = None
    image_paths: Optional[List[str]] = None
    audio_paths: Optional[List[str]] = None


class EvaluationResponse(BaseModel):
    test_id: Optional[int] = None
    score: int
    feedback: str
    suggestions: Optional[str] = None
    model: str
    mock: bool
    result_id: Optional[int] = None


class UploadResponse(BaseModel):
    path: str
    url: str
    filename: str
    size: int
    mime: str
