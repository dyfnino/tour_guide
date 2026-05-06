from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from ..database.session import get_db
from ..models.course import Course
from ..schemas.course import CourseCreate, CourseUpdate, Course as CourseSchema

router = APIRouter(prefix="/courses", tags=["courses"])

@router.get("", response_model=List[CourseSchema])
async def get_courses(
    category: str = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    query = select(Course).where(Course.is_active == True)
    if category:
        query = query.where(Course.category == category)
    result = await db.execute(query.offset(skip).limit(limit))
    courses = result.scalars().all()
    return courses

@router.get("/{course_id}", response_model=CourseSchema)
async def get_course(course_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course).where(Course.id == course_id, Course.is_active == True))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    return course

@router.post("", response_model=CourseSchema, status_code=status.HTTP_201_CREATED)
async def create_course(
    course: CourseCreate,
    db: AsyncSession = Depends(get_db)
):
    db_course = Course(**course.model_dump())
    db.add(db_course)
    await db.commit()
    await db.refresh(db_course)
    return db_course

@router.put("/{course_id}", response_model=CourseSchema)
async def update_course(
    course_id: int,
    course: CourseUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    db_course = result.scalar_one_or_none()
    if not db_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    update_data = course.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_course, field, value)
    
    await db.commit()
    await db.refresh(db_course)
    return db_course

@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    db_course = result.scalar_one_or_none()
    if not db_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    db_course.is_active = False
    await db.commit()
    return None
