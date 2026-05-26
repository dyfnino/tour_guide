from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from ..database.session import get_db
from ..models.live import Live, Replay
from ..models.question import LiveMessage
from ..models.user import User
from ..schemas.live import (
    LiveCreate, LiveUpdate, Live as LiveSchema,
    ReplayCreate, ReplayUpdate, Replay as ReplaySchema
)
from ..schemas.question import LiveMessageCreate, LiveMessageItem
from .auth import get_current_user_optional

router = APIRouter(prefix="/live", tags=["live"])

# 直播相关接口
@router.get("/lives", response_model=List[LiveSchema])
async def get_lives(
    status: str = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    query = select(Live).where(Live.is_active == True)
    if status:
        query = query.where(Live.status == status)
    result = await db.execute(query.offset(skip).limit(limit))
    lives = result.scalars().all()
    return lives

@router.get("/lives/{live_id}", response_model=LiveSchema)
async def get_live(live_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Live).where(Live.id == live_id, Live.is_active == True))
    live = result.scalar_one_or_none()
    if not live:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live not found"
        )
    return live

@router.post("/lives", response_model=LiveSchema, status_code=status.HTTP_201_CREATED)
async def create_live(
    live: LiveCreate,
    db: AsyncSession = Depends(get_db)
):
    db_live = Live(**live.model_dump())
    db.add(db_live)
    await db.commit()
    await db.refresh(db_live)
    return db_live

@router.put("/lives/{live_id}", response_model=LiveSchema)
async def update_live(
    live_id: int,
    live: LiveUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Live).where(Live.id == live_id))
    db_live = result.scalar_one_or_none()
    if not db_live:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live not found"
        )

    prev_status = db_live.status
    update_data = live.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_live, field, value)

    await db.commit()
    await db.refresh(db_live)

    # 直播刚结束，且配置了直播流地址时，自动生成一条回放记录
    if prev_status != "ended" and db_live.status == "ended" and db_live.live_url:
        rres = await db.execute(
            select(Replay).where(Replay.live_id == db_live.id, Replay.is_active == True)
        )
        if not rres.scalars().first():
            # 估算时长：start_time 到 end_time 的差，缺省 0
            duration = 0
            if db_live.start_time and db_live.end_time:
                try:
                    duration = max(0, int((db_live.end_time - db_live.start_time).total_seconds()))
                except Exception:
                    duration = 0
            replay = Replay(
                live_id=db_live.id,
                title=db_live.title + "（回放）",
                description=db_live.description,
                cover_image=db_live.cover_image,
                replay_url=db_live.live_url,
                duration=duration,
                views=0,
            )
            db.add(replay)
            await db.commit()

    return db_live

@router.delete("/lives/{live_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_live(
    live_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Live).where(Live.id == live_id))
    db_live = result.scalar_one_or_none()
    if not db_live:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live not found"
        )
    
    db_live.is_active = False
    await db.commit()
    return None

# 回放相关接口
@router.get("/replays", response_model=List[ReplaySchema])
async def get_replays(
    live_id: int = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    query = select(Replay).where(Replay.is_active == True).order_by(desc(Replay.id))
    if live_id:
        query = query.where(Replay.live_id == live_id)
    result = await db.execute(query.offset(skip).limit(limit))
    replays = result.scalars().all()
    return replays

@router.get("/replays/{replay_id}", response_model=ReplaySchema)
async def get_replay(replay_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Replay).where(Replay.id == replay_id, Replay.is_active == True))
    replay = result.scalar_one_or_none()
    if not replay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Replay not found"
        )
    return replay


@router.post("/replays/{replay_id}/view", response_model=ReplaySchema)
async def increment_replay_view(replay_id: int, db: AsyncSession = Depends(get_db)):
    """回放被观看时调用，将观看次数 +1。"""
    result = await db.execute(select(Replay).where(Replay.id == replay_id, Replay.is_active == True))
    replay = result.scalar_one_or_none()
    if not replay:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Replay not found")
    replay.views = (replay.views or 0) + 1
    await db.commit()
    await db.refresh(replay)
    return replay

@router.post("/replays", response_model=ReplaySchema, status_code=status.HTTP_201_CREATED)
async def create_replay(
    replay: ReplayCreate,
    db: AsyncSession = Depends(get_db)
):
    # 检查直播是否存在
    result = await db.execute(select(Live).where(Live.id == replay.live_id))
    live = result.scalar_one_or_none()
    if not live:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Live not found"
        )
    
    db_replay = Replay(**replay.model_dump())
    db.add(db_replay)
    await db.commit()
    await db.refresh(db_replay)
    return db_replay

@router.put("/replays/{replay_id}", response_model=ReplaySchema)
async def update_replay(
    replay_id: int,
    replay: ReplayUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Replay).where(Replay.id == replay_id))
    db_replay = result.scalar_one_or_none()
    if not db_replay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Replay not found"
        )
    
    update_data = replay.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_replay, field, value)
    
    await db.commit()
    await db.refresh(db_replay)
    return db_replay

@router.delete("/replays/{replay_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_replay(
    replay_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Replay).where(Replay.id == replay_id))
    db_replay = result.scalar_one_or_none()
    if not db_replay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Replay not found"
        )
    
    db_replay.is_active = False
    await db.commit()
    return None


# -------- 直播间聊天消息 --------

@router.get("/lives/{live_id}/messages", response_model=List[LiveMessageItem])
async def get_live_messages(
    live_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """获取最近的直播间消息（按时间倒序，再翻转为正序返回）。"""
    res = await db.execute(
        select(LiveMessage)
        .where(LiveMessage.live_id == live_id)
        .order_by(desc(LiveMessage.id))
        .limit(limit)
    )
    items = list(reversed(res.scalars().all()))
    return items


@router.post("/lives/{live_id}/messages", response_model=LiveMessageItem)
async def send_live_message(
    live_id: int,
    payload: LiveMessageCreate,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """发送直播间消息（已登录使用昵称，否则匿名）"""
    content = (payload.content or "").strip()
    if not content:
        raise HTTPException(400, "消息内容不能为空")
    res = await db.execute(select(Live).where(Live.id == live_id, Live.is_active == True))
    live = res.scalar_one_or_none()
    if not live:
        raise HTTPException(404, "直播不存在")
    msg = LiveMessage(
        live_id=live_id,
        user_id=user.id if user else None,
        nickname=(user.nickname if user else "游客"),
        content=content,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg
