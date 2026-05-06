from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LiveBase(BaseModel):
    title: str
    description: Optional[str] = None
    cover_image: Optional[str] = None
    live_url: Optional[str] = None
    lecturer: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None

class LiveCreate(LiveBase):
    pass

class LiveUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    live_url: Optional[str] = None
    lecturer: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None

class LiveInDB(LiveBase):
    id: int
    viewers: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

class Live(LiveInDB):
    class Config:
        from_attributes = True

class ReplayBase(BaseModel):
    live_id: int
    title: str
    description: Optional[str] = None
    cover_image: Optional[str] = None
    replay_url: Optional[str] = None
    duration: Optional[int] = None

class ReplayCreate(ReplayBase):
    pass

class ReplayUpdate(BaseModel):
    live_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    cover_image: Optional[str] = None
    replay_url: Optional[str] = None
    duration: Optional[int] = None

class ReplayInDB(ReplayBase):
    id: int
    views: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

class Replay(ReplayInDB):
    class Config:
        from_attributes = True
