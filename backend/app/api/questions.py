from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import random
from datetime import datetime

from ..database.session import get_db
from ..models.question import Question, ExamSession
from ..models.user import User
from ..schemas.question import (
    Question as QuestionSchema,
    QuestionPublic,
    QuestionCreate,
    ExamStartRequest, ExamStartResponse,
    ExamSubmitRequest, ExamResult,
)
from .auth import get_current_user

router = APIRouter(tags=["questions & exams"])


# ---------------- 题库（练习） ----------------

@router.get("/questions", response_model=List[QuestionSchema])
async def list_questions(
    category: Optional[str] = None,
    type: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """获取题目（含答案与解析），用于刷题练习页面。"""
    q = select(Question).where(Question.is_active == True)
    if category:
        q = q.where(Question.category == category)
    if type:
        q = q.where(Question.type == type)
    res = await db.execute(q.limit(limit))
    return res.scalars().all()


@router.get("/questions/{qid}", response_model=QuestionSchema)
async def get_question(qid: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Question).where(Question.id == qid, Question.is_active == True))
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "题目不存在")
    return item


@router.post("/questions", response_model=QuestionSchema, status_code=status.HTTP_201_CREATED)
async def create_question(payload: QuestionCreate, db: AsyncSession = Depends(get_db)):
    item = Question(**payload.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


# ---------------- 模拟考试 ----------------

def _is_correct(question: Question, selected: List[int]) -> bool:
    ans = question.answer
    if question.type == "multi":
        if not isinstance(ans, list):
            return False
        return sorted(selected) == sorted(ans)
    # single / judge
    if isinstance(ans, list):
        ans = ans[0] if ans else -1
    return len(selected) == 1 and selected[0] == ans


@router.post("/exams/start", response_model=ExamStartResponse)
async def start_exam(
    payload: ExamStartRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """开始一次模拟考试：从题库随机抽题，创建考试会话。"""
    q = select(Question).where(Question.is_active == True)
    if payload.category:
        q = q.where(Question.category == payload.category)
    res = await db.execute(q)
    pool = res.scalars().all()
    if not pool:
        raise HTTPException(400, "题库为空，请联系管理员")

    count = max(1, min(payload.count or 10, len(pool)))
    chosen = random.sample(pool, count)
    qids = [q.id for q in chosen]

    session = ExamSession(
        user_id=user.id,
        duration=payload.duration or 3600,
        question_ids=qids,
        answers={},
        total=count,
        status="ongoing",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return ExamStartResponse(
        exam_id=session.id,
        duration=session.duration,
        questions=[QuestionPublic.model_validate(q) for q in chosen],
    )


@router.post("/exams/{exam_id}/submit", response_model=ExamResult)
async def submit_exam(
    exam_id: int,
    payload: ExamSubmitRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    res = await db.execute(select(ExamSession).where(ExamSession.id == exam_id))
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "考试会话不存在")
    if session.user_id != user.id:
        raise HTTPException(403, "无权操作他人的考试会话")
    if session.status != "ongoing":
        # 已交卷直接返回结果
        return ExamResult(
            exam_id=session.id,
            score=session.score or 0,
            correct_count=session.correct_count or 0,
            total=session.total or 0,
            status=session.status,
        )

    # 评分
    qres = await db.execute(select(Question).where(Question.id.in_(session.question_ids)))
    qmap = {q.id: q for q in qres.scalars().all()}

    correct = 0
    for qid in session.question_ids:
        q = qmap.get(qid)
        sel = payload.answers.get(str(qid)) or payload.answers.get(qid) or []
        if q and _is_correct(q, list(sel)):
            correct += 1

    total = session.total or len(session.question_ids)
    score = round(correct / total * 100) if total else 0

    session.answers = {str(k): v for k, v in payload.answers.items()}
    session.correct_count = correct
    session.score = score
    session.status = "submitted"
    session.submitted_at = datetime.utcnow()
    await db.commit()
    await db.refresh(session)

    return ExamResult(
        exam_id=session.id,
        score=score,
        correct_count=correct,
        total=total,
        status=session.status,
    )


@router.get("/exams/{exam_id}", response_model=ExamResult)
async def get_exam(
    exam_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    res = await db.execute(select(ExamSession).where(ExamSession.id == exam_id))
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "考试会话不存在")
    if session.user_id != user.id:
        raise HTTPException(403, "无权访问")
    return ExamResult(
        exam_id=session.id,
        score=session.score or 0,
        correct_count=session.correct_count or 0,
        total=session.total or 0,
        status=session.status,
    )