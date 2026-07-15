from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from ..database.session import Base

class AiTest(Base):
    __tablename__ = "ai_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    type = Column(String(50))  # 测评类型：theory, lecture, interview
    difficulty = Column(String(20))  # 难度级别
    duration = Column(Integer)  # 预计时长（分钟）
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class TestResult(Base):
    __tablename__ = "test_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    test_id = Column(Integer)
    score = Column(Integer)  # 分数
    result = Column(Text)  # 测评结果详情
    feedback = Column(Text)  # AI反馈
    created_at = Column(DateTime(timezone=True), server_default=func.now())
