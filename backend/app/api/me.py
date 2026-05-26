from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime

from ..database.session import get_db
from ..models.question import UserCourse
from ..models.course import Course
from ..models.user import User
from ..schemas.question import UserCourseItem, ProgressUpdate
from .auth import get_current_user

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/courses", response_model=List[UserCourseItem])
async def my_courses(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    res = await db.execute(select(UserCourse).where(UserCourse.user_id == user.id))
    return res.scalars().all()


@router.get("/courses/detail", response_model=List[dict])
async def my_courses_detail(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """返回我的课程列表（含课程详情，便于前端直接渲染）"""
    res = await db.execute(select(UserCourse).where(UserCourse.user_id == user.id))
    items = res.scalars().all()
    if not items:
        return []
    course_ids = [i.course_id for i in items]
    cres = await db.execute(select(Course).where(Course.id.in_(course_ids)))
    cmap = {c.id: c for c in cres.scalars().all()}
    out = []
    for it in items:
        c = cmap.get(it.course_id)
        if not c:
            continue
        out.append({
            "id": c.id,
            "name": c.name,
            "image": c.image,
            "desc": c.description,
            "lecturer": (c.level or ""),
            "category": c.category,
            "media_type": c.media_type or "video",
            "media_url": c.media_url or "",
            "progress": it.progress,
            "last_studied_at": it.last_studied_at,
        })
    return out


@router.post("/courses/{course_id}/enroll", response_model=UserCourseItem)
async def enroll_course(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """加入学习"""
    cres = await db.execute(select(Course).where(Course.id == course_id, Course.is_active == True))
    course = cres.scalar_one_or_none()
    if not course:
        raise HTTPException(404, "课程不存在")
    res = await db.execute(
        select(UserCourse).where(UserCourse.user_id == user.id, UserCourse.course_id == course_id)
    )
    rec = res.scalar_one_or_none()
    if not rec:
        rec = UserCourse(user_id=user.id, course_id=course_id, progress=0)
        db.add(rec)
        await db.commit()
        await db.refresh(rec)
    return rec


@router.put("/courses/{course_id}/progress", response_model=UserCourseItem)
async def update_progress(
    course_id: int,
    payload: ProgressUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    res = await db.execute(
        select(UserCourse).where(UserCourse.user_id == user.id, UserCourse.course_id == course_id)
    )
    rec = res.scalar_one_or_none()
    if not rec:
        raise HTTPException(404, "尚未加入该课程")
    rec.progress = max(0, min(100, payload.progress))
    rec.last_studied_at = datetime.utcnow()
    await db.commit()
    await db.refresh(rec)
    return rec