"""
通用文件上传接口。

- POST /api/uploads          上传文件，返回 {path, url, filename, size, mime, kind}
- GET  /api/uploads/files/{kind}/{name}   下载（也可走静态文件，但保留作为兜底）

支持 kind=image / video / audio，对应不同的扩展名白名单和大小限制。
所有文件保存到 backend/uploads/{kind}/ 目录下，前端通过完整 URL 访问。
"""
import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Form
from fastapi.responses import FileResponse

from ..models.user import User
from .auth import get_current_user_optional


router = APIRouter(prefix="/uploads", tags=["uploads"])


# 后端 uploads 根目录（绝对路径）
UPLOAD_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
os.makedirs(UPLOAD_ROOT, exist_ok=True)

# 各 kind 的子目录
KIND_DIRS = {
    "image": "images",
    "video": "videos",
    "audio": "audios",
}

ALLOWED_EXT = {
    "image": {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"},
    "video": {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv"},
    "audio": {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".silk"},
}

MAX_SIZE = {
    "image": 10 * 1024 * 1024,        # 10 MB
    "video": 500 * 1024 * 1024,       # 500 MB
    "audio": 100 * 1024 * 1024,       # 100 MB
}


def _ensure_kind_dir(kind: str) -> str:
    sub = KIND_DIRS.get(kind)
    if not sub:
        raise HTTPException(400, f"不支持的 kind: {kind}")
    d = os.path.join(UPLOAD_ROOT, sub)
    os.makedirs(d, exist_ok=True)
    return d


@router.post("")
async def upload_file(
    request: Request,
    kind: str = Form(...),
    file: UploadFile = File(...),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """上传单个文件。kind=image/video/audio。返回完整可访问 URL。"""
    kind = (kind or "").lower()
    if kind not in ALLOWED_EXT:
        raise HTTPException(400, f"非法 kind: {kind}（允许 image/video/audio）")

    fname = file.filename or "upload"
    ext = os.path.splitext(fname)[1].lower()
    if ext not in ALLOWED_EXT[kind]:
        raise HTTPException(400, f"不支持的文件扩展名: {ext}（{kind} 仅支持 {sorted(ALLOWED_EXT[kind])}）")

    content = await file.read()
    if len(content) > MAX_SIZE[kind]:
        raise HTTPException(400, f"文件过大（>{MAX_SIZE[kind] // (1024*1024)}MB）")

    target_dir = _ensure_kind_dir(kind)
    safe_name = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(target_dir, safe_name)
    with open(save_path, "wb") as f:
        f.write(content)

    base = str(request.base_url).rstrip("/")
    url = f"{base}/uploads/{KIND_DIRS[kind]}/{safe_name}"

    return {
        "path": save_path,
        "url": url,
        "filename": fname,
        "size": len(content),
        "mime": file.content_type or "",
        "kind": kind,
        "relative": f"/uploads/{KIND_DIRS[kind]}/{safe_name}",
    }


@router.get("/files/{kind}/{name}")
async def download_file(kind: str, name: str):
    """下载/访问已上传的文件。也可以直接走 main.py 挂的 StaticFiles。"""
    if "/" in name or "\\" in name or ".." in name:
        raise HTTPException(400, "非法文件名")
    sub = KIND_DIRS.get(kind)
    if not sub:
        raise HTTPException(400, f"非法 kind: {kind}")
    path = os.path.join(UPLOAD_ROOT, sub, name)
    if not os.path.exists(path):
        raise HTTPException(404, "文件不存在")
    return FileResponse(path)