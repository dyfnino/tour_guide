from pydantic import BaseModel
from typing import Optional
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
