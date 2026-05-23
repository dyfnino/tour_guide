from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime


class QuestionBase(BaseModel):
    type: str
    title: str
    options: List[str]
    answer: Any
    analysis: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = "normal"


class QuestionCreate(QuestionBase):
    pass


class Question(QuestionBase):
    id: int

    class Config:
        from_attributes = True


# 题目（不带答案，用于考试出题时返回前端）
class QuestionPublic(BaseModel):
    id: int
    type: str
    title: str
    options: List[str]
    category: Optional[str] = None
    difficulty: Optional[str] = None

    class Config:
        from_attributes = True


# 考试相关
class ExamStartRequest(BaseModel):
    count: Optional[int] = 10
    duration: Optional[int] = 3600
    category: Optional[str] = None


class ExamStartResponse(BaseModel):
    exam_id: int
    duration: int
    questions: List[QuestionPublic]


class ExamSubmitRequest(BaseModel):
    answers: Dict[str, List[int]]   # {"qid": [选项索引,...]}


class ExamResult(BaseModel):
    exam_id: int
    score: int
    correct_count: int
    total: int
    status: str

    class Config:
        from_attributes = True


# 学习进度
class UserCourseItem(BaseModel):
    id: int
    course_id: int
    progress: int
    last_studied_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProgressUpdate(BaseModel):
    progress: int   # 0-100


# 直播间消息
class LiveMessageCreate(BaseModel):
    content: str


class LiveMessageItem(BaseModel):
    id: int
    nickname: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True