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
  DASHSCOPE_API_KEY: API Key（必填，缺失时会抛出运行时错误）
  QWEN_TEXT_MODEL: 文本模型，默认 qwen-plus
  QWEN_VL_MODEL: 视觉模型，默认 qwen-vl-max
  QWEN_AUDIO_MODEL: 语音模型，默认 qwen-audio-turbo
  QWEN_OMNI_MODEL: 全模态模型，默认 qwen-omni-turbo

注意：本模块已彻底移除 mock 模式，所有请求均走真实 Qwen 多模态服务。
"""
import os
import base64
import json
import requests
from typing import List, Dict, Any, Optional


DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_TIMEOUT = 60


def _api_key() -> str:
    key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "DASHSCOPE_API_KEY 未配置：请在 backend/.env 中设置阿里云 DashScope API Key。"
        )
    return key


def is_mock() -> bool:
    """已废弃：mock 模式已被彻底移除，始终返回 False。"""
    return False


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
        # DashScope 兼容模式要求 input_audio.data 为完整 data URL（含 data:audio/...;base64, 前缀）
        fmt = "mp3"
        if p.lower().endswith(".wav"): fmt = "wav"
        elif p.lower().endswith(".m4a"): fmt = "m4a"
        elif p.lower().endswith(".aac"): fmt = "aac"
        data_url = _file_to_data_url(p, _guess_mime(p))
        parts.append({"type": "input_audio", "input_audio": {"data": data_url, "format": fmt}})
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
    统一调用入口。始终走真实 Qwen 多模态服务，返回：
        {"text": str, "model": str, "mock": False, "usage": dict|None, "raw": dict|None}
    调用失败会返回 error=True 的错误对象，但不会再降级为 mock 内容。
    """
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

    # qwen-omni 系列在兼容模式下仅支持流式；此处若命中 Omni，则内部改走流式聚合
    if "omni" in chosen_model:
        acc, usage, model_used = "", None, chosen_model
        for ev in chat_completion_stream(
            user_text=user_text, system_prompt=system_prompt, history=history,
            image_paths=image_paths, image_urls=image_urls,
            audio_paths=audio_paths, audio_urls=audio_urls,
            model=chosen_model, temperature=temperature, max_tokens=max_tokens,
        ):
            t = ev.get("type")
            if t == "delta":
                acc += ev.get("text", "")
            elif t == "done":
                usage = ev.get("usage")
            elif t == "error":
                return {"text": ev.get("text", "AI 出错"), "model": model_used,
                        "mock": False, "usage": None, "raw": None, "error": True}
        return {"text": acc or "（模型未返回内容）", "model": model_used,
                "mock": False, "usage": usage, "raw": None}

    try:
        api_key = _api_key()
    except RuntimeError as e:
        return {
            "text": f"AI 服务未配置：{e}",
            "model": chosen_model, "mock": False, "usage": None, "raw": None,
            "error": True,
        }

    headers = {
        "Authorization": f"Bearer {api_key}",
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


def chat_completion_stream(
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
):
    """
    流式调用生成器。逐块 yield 事件字典：
        {"type": "meta",  "model": str}                 # 首个事件，告知模型名
        {"type": "delta", "text": str}                  # 文本增量
        {"type": "done",  "usage": dict|None}           # 结束
        {"type": "error", "text": str}                  # 出错
    基于 DashScope OpenAI 兼容协议 stream=True（SSE）。
    """
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
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    # qwen-omni 系列（兼容模式）要求指定输出模态，且只能流式
    if "omni" in chosen_model:
        payload["modalities"] = ["text"]

    try:
        api_key = _api_key()
    except RuntimeError as e:
        yield {"type": "error", "text": f"AI 服务未配置：{e}", "model": chosen_model}
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    yield {"type": "meta", "model": chosen_model}

    try:
        with requests.post(
            f"{DASHSCOPE_BASE_URL}/chat/completions",
            headers=headers,
            data=json.dumps(payload),
            timeout=DEFAULT_TIMEOUT,
            stream=True,
        ) as r:
            r.raise_for_status()
            usage = None
            for raw_line in r.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue
                line = raw_line.strip()
                if not line.startswith("data:"):
                    continue
                data_str = line[len("data:"):].strip()
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                except Exception:
                    continue
                if chunk.get("usage"):
                    usage = chunk["usage"]
                choices = chunk.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                piece = delta.get("content")
                if isinstance(piece, list):
                    piece = "".join(
                        (p.get("text") or "") for p in piece if isinstance(p, dict)
                    )
                if piece:
                    yield {"type": "delta", "text": piece}
            yield {"type": "done", "usage": usage, "model": chosen_model}
    except requests.HTTPError as e:
        body = ""
        try: body = e.response.text
        except Exception: pass
        yield {"type": "error", "text": f"AI 服务调用失败：{e}（{body[:200]}）", "model": chosen_model}
    except Exception as e:
        yield {"type": "error", "text": f"AI 服务调用异常：{e}", "model": chosen_model}