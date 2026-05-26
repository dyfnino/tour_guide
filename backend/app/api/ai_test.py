import os
import re
import uuid
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database.session import get_db
from ..models.ai_test import AiTest, TestResult
from ..models.user import User
from ..schemas.ai_test import (
    AiTestCreate, AiTestUpdate, AiTest as AiTestSchema,
    TestResultCreate, TestResult as TestResultSchema,
    ChatRequest, ChatResponse,
    EvaluationRequest, EvaluationResponse,
    UploadResponse,
)
from ..utils import qwen
from .auth import get_current_user_optional

router = APIRouter(prefix="/ai-test", tags=["ai-test"])


# ---- 上传目录 ----
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
UPLOAD_DIR = os.path.abspath(UPLOAD_DIR)
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
ALLOWED_AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".silk"}


# ============= 测评类型 CRUD（保留）=============

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
    return result.scalars().all()


@router.get("/tests/{test_id}", response_model=AiTestSchema)
async def get_ai_test(test_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AiTest).where(AiTest.id == test_id, AiTest.is_active == True))
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI test not found")
    return test


@router.post("/tests", response_model=AiTestSchema, status_code=status.HTTP_201_CREATED)
async def create_ai_test(test: AiTestCreate, db: AsyncSession = Depends(get_db)):
    db_test = AiTest(**test.model_dump())
    db.add(db_test)
    await db.commit()
    await db.refresh(db_test)
    return db_test


@router.put("/tests/{test_id}", response_model=AiTestSchema)
async def update_ai_test(test_id: int, test: AiTestUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AiTest).where(AiTest.id == test_id))
    db_test = result.scalar_one_or_none()
    if not db_test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI test not found")
    for f, v in test.model_dump(exclude_unset=True).items():
        setattr(db_test, f, v)
    await db.commit()
    await db.refresh(db_test)
    return db_test


@router.delete("/tests/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ai_test(test_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AiTest).where(AiTest.id == test_id))
    db_test = result.scalar_one_or_none()
    if not db_test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI test not found")
    db_test.is_active = False
    await db.commit()
    return None


# ============= 测评结果（保留）=============

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
    return result.scalars().all()


@router.post("/results", response_model=TestResultSchema, status_code=status.HTTP_201_CREATED)
async def create_test_result(result: TestResultCreate, db: AsyncSession = Depends(get_db)):
    test_result = await db.execute(select(AiTest).where(AiTest.id == result.test_id))
    if not test_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI test not found")
    db_result = TestResult(**result.model_dump())
    db.add(db_result)
    await db.commit()
    await db.refresh(db_result)
    return db_result


# ============= 文件上传（图片/音频）=============

@router.post("/upload", response_model=UploadResponse)
async def upload_media(
    request: Request,
    file: UploadFile = File(...),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """接收图片/音频上传，返回服务器临时路径，供后续 chat / evaluate 调用。"""
    fname = file.filename or "upload"
    ext = os.path.splitext(fname)[1].lower()
    if ext not in ALLOWED_IMAGE_EXT and ext not in ALLOWED_AUDIO_EXT:
        raise HTTPException(400, f"不支持的文件类型: {ext}")

    safe_id = uuid.uuid4().hex
    safe_name = f"{safe_id}{ext}"
    save_path = os.path.join(UPLOAD_DIR, safe_name)

    content = await file.read()
    if len(content) > 30 * 1024 * 1024:  # 30MB
        raise HTTPException(400, "文件过大（>30MB）")
    with open(save_path, "wb") as f:
        f.write(content)

    base = str(request.base_url).rstrip("/")
    url = f"{base}/api/ai-test/files/{safe_name}"
    return UploadResponse(
        path=save_path,
        url=url,
        filename=fname,
        size=len(content),
        mime=file.content_type or "",
    )


@router.get("/files/{name}")
async def download_media(name: str):
    """简易下载/访问已上传的文件。"""
    # 防止路径穿越
    if "/" in name or "\\" in name or ".." in name:
        raise HTTPException(400, "非法文件名")
    path = os.path.join(UPLOAD_DIR, name)
    if not os.path.exists(path):
        raise HTTPException(404, "文件不存在")
    return FileResponse(path)


# ============= AI 对话 =============

CHAT_SYSTEM_PROMPT = (
    "你是一名经验丰富的中国导游资格考试辅导老师，"
    "精通《全国导游基础知识》《政策与法律法规》《导游业务》《地方导游基础知识》"
    "以及导游词撰写与讲解技巧。请用简洁、亲切、可执行的中文回答用户的问题，"
    "必要时给出条目化要点；用户提供图片时请先简述画面，再结合导游知识答题。"
)


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    payload: ChatRequest,
    user: Optional[User] = Depends(get_current_user_optional),
):
    history = [h.model_dump() for h in (payload.history or [])]
    res = qwen.chat_completion(
        user_text=payload.message,
        system_prompt=CHAT_SYSTEM_PROMPT,
        history=history,
        image_urls=payload.image_urls,
        audio_urls=payload.audio_urls,
        image_paths=payload.image_paths,
        audio_paths=payload.audio_paths,
    )
    return ChatResponse(
        text=res.get("text", ""),
        model=res.get("model", "unknown"),
        mock=bool(res.get("mock")),
        usage=res.get("usage"),
    )


# ============= AI 测评（理论/讲解/面试）=============

EVAL_PROMPTS = {
    "theory": (
        "你正在为导游资格考生进行【理论知识测评】。请基于考生的回答，从'知识准确度'、"
        "'要点完整度'、'表达逻辑'三个维度打分，给出 0~100 的总分，并指出错误与改进建议。"
        "请严格按以下 JSON 输出，不要多余文本：\n"
        "{\"score\": <int>, \"feedback\": \"...\", \"suggestions\": \"...\"}"
    ),
    "lecture": (
        "你正在评估考生的【导游词讲解】。请综合考虑：内容准确性、讲解条理、语言表现力、"
        "感染力，从 0~100 打分。如果用户提供了音频，请基于语音内容评估；如有图片，"
        "请结合画面（景点）评估。严格按 JSON 输出：\n"
        "{\"score\": <int>, \"feedback\": \"...\", \"suggestions\": \"...\"}"
    ),
    "interview": (
        "你正在主持导游资格【面试模拟测评】。请就考生的回答从仪表表达、应变能力、"
        "专业素养、礼貌用语四方面综合评估，给 0~100 总分。严格按 JSON 输出：\n"
        "{\"score\": <int>, \"feedback\": \"...\", \"suggestions\": \"...\"}"
    ),
}


def _parse_eval_json(text: str):
    """从模型输出中尽量解析 JSON。"""
    if not text:
        return None
    # 截取 JSON 段
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None


@router.post("/evaluate", response_model=EvaluationResponse)
async def ai_evaluate(
    payload: EvaluationRequest,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
):
    test_type = (payload.test_type or "theory").lower()
    sys_prompt = EVAL_PROMPTS.get(test_type, EVAL_PROMPTS["theory"])

    user_text_parts = []
    if payload.topic:
        user_text_parts.append(f"题目/主题：{payload.topic}")
    if payload.user_answer:
        user_text_parts.append(f"考生回答：{payload.user_answer}")
    if not user_text_parts and not (payload.image_paths or payload.image_urls or
                                     payload.audio_paths or payload.audio_urls):
        raise HTTPException(400, "请至少提供答题文本、图片或音频之一")
    user_text = "\n".join(user_text_parts) if user_text_parts else "请基于上传素材进行测评。"

    res = qwen.chat_completion(
        user_text=user_text,
        system_prompt=sys_prompt,
        image_urls=payload.image_urls,
        audio_urls=payload.audio_urls,
        image_paths=payload.image_paths,
        audio_paths=payload.audio_paths,
        temperature=0.3,
        max_tokens=1024,
    )
    text = res.get("text", "")
    parsed = _parse_eval_json(text) or {}
    score = int(parsed.get("score") or 0)
    score = max(0, min(100, score))
    feedback = parsed.get("feedback") or text or "（未生成评语）"
    suggestions = parsed.get("suggestions") or ""

    # 持久化（test_id 可选）
    result_id = None
    if payload.test_id and user:
        try:
            db_result = TestResult(
                user_id=user.id,
                test_id=payload.test_id,
                score=score,
                result=feedback[:2000],
                feedback=suggestions[:2000] if suggestions else None,
            )
            db.add(db_result)
            await db.commit()
            await db.refresh(db_result)
            result_id = db_result.id
        except Exception:
            await db.rollback()

    return EvaluationResponse(
        test_id=payload.test_id,
        score=score,
        feedback=feedback,
        suggestions=suggestions,
        model=res.get("model", "unknown"),
        mock=bool(res.get("mock")),
        result_id=result_id,
    )