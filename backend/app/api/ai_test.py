from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from ..database.session import get_db
from ..models.ai_test import AiTest, TestResult
from ..schemas.ai_test import (
    AiTestCreate, AiTestUpdate, AiTest as AiTestSchema,
    TestResultCreate, TestResult as TestResultSchema
)

router = APIRouter(prefix="/ai-test", tags=["ai-test"])

# AI测评相关接口
@router.get("/tests", response_model=List[AiTestSchema])
async def get_ai_tests(
    type: str = None,
    difficulty: str = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    query = select(AiTest).where(AiTest.is_active == True)
    if type:
        query = query.where(AiTest.type == type)
    if difficulty:
        query = query.where(AiTest.difficulty == difficulty)
    result = await db.execute(query.offset(skip).limit(limit))
    tests = result.scalars().all()
    return tests

@router.get("/tests/{test_id}", response_model=AiTestSchema)
async def get_ai_test(test_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AiTest).where(AiTest.id == test_id, AiTest.is_active == True))
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI test not found"
        )
    return test

@router.post("/tests", response_model=AiTestSchema, status_code=status.HTTP_201_CREATED)
async def create_ai_test(
    test: AiTestCreate,
    db: AsyncSession = Depends(get_db)
):
    db_test = AiTest(**test.model_dump())
    db.add(db_test)
    await db.commit()
    await db.refresh(db_test)
    return db_test

@router.put("/tests/{test_id}", response_model=AiTestSchema)
async def update_ai_test(
    test_id: int,
    test: AiTestUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AiTest).where(AiTest.id == test_id))
    db_test = result.scalar_one_or_none()
    if not db_test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI test not found"
        )
    
    update_data = test.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_test, field, value)
    
    await db.commit()
    await db.refresh(db_test)
    return db_test

@router.delete("/tests/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_test(
    test_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AiTest).where(AiTest.id == test_id))
    db_test = result.scalar_one_or_none()
    if not db_test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI test not found"
        )
    
    db_test.is_active = False
    await db.commit()
    return None

# 测评结果相关接口
@router.get("/results", response_model=List[TestResultSchema])
async def get_test_results(
    user_id: int = None,
    test_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    query = select(TestResult)
    if user_id:
        query = query.where(TestResult.user_id == user_id)
    if test_id:
        query = query.where(TestResult.test_id == test_id)
    result = await db.execute(query.offset(skip).limit(limit))
    results = result.scalars().all()
    return results

@router.post("/results", response_model=TestResultSchema, status_code=status.HTTP_201_CREATED)
async def create_test_result(
    result: TestResultCreate,
    db: AsyncSession = Depends(get_db)
):
    # 检查测评是否存在
    test_result = await db.execute(select(AiTest).where(AiTest.id == result.test_id))
    test = test_result.scalar_one_or_none()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI test not found"
        )
    
    db_result = TestResult(**result.model_dump())
    db.add(db_result)
    await db.commit()
    await db.refresh(db_result)
    return db_result
