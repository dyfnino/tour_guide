"""
阿里云 DashScope (Qwen) 多模态接入封装

功能：
1. 纯文本对话：qwen-plus / qwen-turbo
2. 视觉理解（图片+文本）：qwen-vl-max / qwen-vl-plus
3. 语音理解（音频+文本）：qwen-audio-turbo
4. 全模态（图+音+文）：qwen-omni-turbo

使用 OpenAI 兼容协议（DashScope 提供）：
  https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions

环境变量：
  DASHSCOPE_API_KEY: API Key（缺失时自动 mock）
  QWEN_TEXT_MODEL: 文本模型，默认 qwen-plus
  QWEN_VL_MODEL: 视觉模型，默认 qwen-vl-max
  QWEN_AUDIO_MODEL: 语音模型，默认 qwen-audio-turbo
  QWEN_OMNI_MODEL: 全模态模型，默认 qwen-omni-turbo
  QWEN_MOCK: 1 时强制使用 mock 返回，便于本地联调
"""
import os
import base64
import json
import requests
from typing import List, Dict, Any, Optional


DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_TIMEOUT = 60


def _api_key() -> str:
    return os.getenv("DASHSCOPE_API_KEY", "").strip()


def is_mock() -> bool:
    """是否处于 mock 模式：显式开启或 API Key 缺失。"""
    if os.getenv("QWEN_MOCK", "0").strip() == "1":
        return True
    return not _api_key()


def _model_text() -> str:
    return os.getenv("QWEN_TEXT_MODEL", "qwen-plus")


def _model_vl() -> str:
    return os.getenv("QWEN_VL_MODEL", "qwen-vl-max")


def _model_audio() -> str:
    return os.getenv("QWEN_AUDIO_MODEL", "qwen-audio-turbo")


def _model_omni() -> str:
    return os.getenv("QWEN_OMNI_MODEL", "qwen-omni-turbo")


def _file_to_data_url(path: str, mime_hint: Optional[str] = None) -> str:
    """读取本地文件转成 data URL（base64）。"""
    with open(path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode("utf-8")
    mime = mime_hint or _guess_mime(path)
    return f"data:{mime};base64,{b64}"


def _guess_mime(path: str) -> str:
    p = path.lower()
    if p.endswith(".png"): return "image/png"
    if p.endswith(".jpg") or p.endswith(".jpeg"): return "image/jpeg"
    if p.endswith(".webp"): return "image/webp"
    if p.endswith(".gif"): return "image/gif"
    if p.endswith(".mp3"): return "audio/mpeg"
    if p.endswith(".wav"): return "audio/wav"
    if p.endswith(".m4a"): return "audio/mp4"
    if p.endswith(".aac"): return "audio/aac"
    if p.endswith(".silk"): return "audio/silk"
    return "application/octet-stream"


def _build_multimodal_content(
    text: Optional[str],
    image_paths: Optional[List[str]] = None,
    image_urls: Optional[List[str]] = None,
    audio_paths: Optional[List[str]] = None,
    audio_urls: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    parts: List[Dict[str, Any]] = []
    for u in (image_urls or []):
        parts.append({"type": "image_url", "image_url": {"url": u}})
    for p in (image_paths or []):
        parts.append({"type": "image_url", "image_url": {"url": _file_to_data_url(p)}})
    for u in (audio_urls or []):
        parts.append({"type": "input_audio", "input_audio": {"data": u, "format": "mp3"}})
    for p in (audio_paths or []):
        # OpenAI 兼容的 audio 入参用 data URL 方式
        with open(p, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        fmt = "mp3"
        if p.lower().endswith(".wav"): fmt = "wav"
        elif p.lower().endswith(".m4a"): fmt = "m4a"
        elif p.lower().endswith(".aac"): fmt = "aac"
        parts.append({"type": "input_audio", "input_audio": {"data": b64, "format": fmt}})
    if text:
        parts.append({"type": "text", "text": text})
    return parts


def _choose_model(image_paths, image_urls, audio_paths, audio_urls) -> str:
    has_img = bool(image_paths or image_urls)
    has_aud = bool(audio_paths or audio_urls)
    if has_img and has_aud:
        return _model_omni()
    if has_aud:
        return _model_audio()
    if has_img:
        return _model_vl()
    return _model_text()


def chat_completion(
    user_text: Optional[str],
    system_prompt: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None,
    image_paths: Optional[List[str]] = None,
    image_urls: Optional[List[str]] = None,
    audio_paths: Optional[List[str]] = None,
    audio_urls: Optional[List[str]] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> Dict[str, Any]:
    """
    统一调用入口。返回：
        {"text": str, "model": str, "mock": bool, "usage": dict|None, "raw": dict|None}
    """
    if is_mock():
        return _mock_reply(user_text, image_paths, image_urls, audio_paths, audio_urls)

    chosen_model = model or _choose_model(image_paths, image_urls, audio_paths, audio_urls)

    messages: List[Dict[str, Any]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if history:
        for h in history:
            role = h.get("role")
            content = h.get("content")
            if role and content:
                messages.append({"role": role, "content": content})

    parts = _build_multimodal_content(user_text, image_paths, image_urls, audio_paths, audio_urls)
    if not parts:
        parts = [{"type": "text", "text": user_text or ""}]
    messages.append({"role": "user", "content": parts})

    payload: Dict[str, Any] = {
        "model": chosen_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    headers = {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }

    try:
        r = requests.post(
            f"{DASHSCOPE_BASE_URL}/chat/completions",
            headers=headers,
            data=json.dumps(payload),
            timeout=DEFAULT_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        text = ""
        try:
            text = data["choices"][0]["message"]["content"]
            if isinstance(text, list):
                # 兼容 content 是数组结构（多模态返回）
                text = "".join(
                    (p.get("text") or "") for p in text if isinstance(p, dict)
                )
        except Exception:
            text = ""
        return {
            "text": text or "（模型未返回内容）",
            "model": chosen_model,
            "mock": False,
            "usage": data.get("usage"),
            "raw": data,
        }
    except requests.HTTPError as e:
        body = ""
        try: body = e.response.text
        except Exception: pass
        return {
            "text": f"AI 服务调用失败：{e}（{body[:200]}）",
            "model": chosen_model, "mock": False, "usage": None, "raw": None,
            "error": True,
        }
    except Exception as e:
        return {
            "text": f"AI 服务调用异常：{e}",
            "model": chosen_model, "mock": False, "usage": None, "raw": None,
            "error": True,
        }


def _mock_reply(user_text, image_paths, image_urls, audio_paths, audio_urls) -> Dict[str, Any]:
    parts = []
    if user_text: parts.append(f"我理解到你的问题是：{user_text}")
    if image_paths or image_urls:
        n = len(image_paths or []) + len(image_urls or [])
        parts.append(f"已收到 {n} 张图片，模拟视觉分析：图中应为风景照（mock）。")
    if audio_paths or audio_urls:
        n = len(audio_paths or []) + len(audio_urls or [])
        parts.append(f"已收到 {n} 段音频，模拟语音识别：内容大致是导游词讲解（mock）。")
    if not parts:
        parts.append("（mock）你好，我是导游 AI 助手，请问有什么可以帮你？")
    parts.append("\n\n💡 提示：当前为 Mock 模式，配置 DASHSCOPE_API_KEY 后将切换为真实 Qwen 多模态模型。")
    return {
        "text": "\n".join(parts),
        "model": "mock-qwen",
        "mock": True,
        "usage": None,
        "raw": None,
    }