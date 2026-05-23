from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database.session import Base


class Question(Base):
    """题库题目"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(20), nullable=False)            # single / multi / judge
    title = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)               # ["A选项","B选项",...]
    answer = Column(JSON, nullable=False)                # 单选/判断: int; 多选: [int,...]
    analysis = Column(Text)
    category = Column(String(50))                        # basic/business/policy/local
    difficulty = Column(String(20), default="normal")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ExamSession(Base):
    """模拟考试会话"""
    __tablename__ = "exam_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    duration = Column(Integer, default=3600)              # 秒
    question_ids = Column(JSON, nullable=False)           # 出题列表 [id,...]
    answers = Column(JSON, default=dict)                  # {qid: [选项索引]}
    score = Column(Integer)
    correct_count = Column(Integer)
    total = Column(Integer, default=0)
    status = Column(String(20), default="ongoing")        # ongoing/submitted/timeout
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    submitted_at = Column(DateTime(timezone=True))


class UserCourse(Base):
    """用户课程学习进度"""
    __tablename__ = "user_courses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    progress = Column(Integer, default=0)                 # 0-100
    last_studied_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LiveMessage(Base):
    """直播间聊天消息"""
    __tablename__ = "live_messages"

    id = Column(Integer, primary_key=True, index=True)
    live_id = Column(Integer, ForeignKey("lives.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    nickname = Column(String(50), nullable=False, default="匿名")
    content = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())