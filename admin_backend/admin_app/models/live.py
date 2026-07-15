from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from ..database.session import Base

class Live(Base):
    __tablename__ = "lives"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    cover_image = Column(String(255))
    live_url = Column(String(255))
    lecturer = Column(String(50))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    status = Column(String(20))  # 状态：upcoming, live, ended
    viewers = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Replay(Base):
    __tablename__ = "replays"
    
    id = Column(Integer, primary_key=True, index=True)
    live_id = Column(Integer)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    cover_image = Column(String(255))
    replay_url = Column(String(255))
    duration = Column(Integer)  # 时长（秒）
    views = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
