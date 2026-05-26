from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import requests
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
import os
from pydantic import BaseModel
from dotenv import load_dotenv

from ..database.session import get_db
from ..models.user import User
from ..schemas.user import WechatLogin, LoginResponse, User as UserSchema

load_dotenv()

router = APIRouter(prefix="/auth", tags=["authentication"])

# 微信小程序配置
WECHAT_APPID = os.getenv("WECHAT_APPID", "").strip()
WECHAT_SECRET = os.getenv("WECHAT_SECRET", "").strip()
WECHAT_LOGIN_URL = "https://api.weixin.qq.com/sns/jscode2session"

# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY", "guide-platform-dev-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 天

pwd_context = None  # 已替换为直接使用 bcrypt


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)





# 通过 Authorization 头获取当前用户（可选，未登录返回 None）
async def get_current_user_optional(
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub", 0))
    except (JWTError, ValueError):
        return None
    if not user_id:
        return None
    res = await db.execute(select(User).where(User.id == user_id))
    return res.scalar_one_or_none()


# 强制要求登录
async def get_current_user(
    user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录或登录已过期")
    return user


class WechatProfile(BaseModel):
    """前端 wx.getUserProfile 返回的 userInfo"""
    code: str
    nickName: Optional[str] = None
    avatarUrl: Optional[str] = None


async def _build_login_response(user: User) -> LoginResponse:
    token = create_access_token({"sub": str(user.id)})
    return LoginResponse(access_token=token, user=UserSchema.model_validate(user))


@router.post("/wechat", response_model=LoginResponse)
async def wechat_login(payload: WechatProfile, db: AsyncSession = Depends(get_db)):
    """
    微信小程序登录。
    - 必须传入 wx.login 拿到的 code；
    - 可选传入 nickName / avatarUrl（来自 wx.getUserProfile），用于首次入库；
    - 未配置 WECHAT_APPID/SECRET 时走开发态：用 dev_<code> 当 openid 自动建用户。
    """
    openid: Optional[str] = None
    session_key: Optional[str] = None

    if WECHAT_APPID and WECHAT_SECRET:
        try:
            resp = requests.get(
                WECHAT_LOGIN_URL,
                params={
                    "appid": WECHAT_APPID,
                    "secret": WECHAT_SECRET,
                    "js_code": payload.code,
                    "grant_type": "authorization_code",
                },
                timeout=8,
            )
            data = resp.json()
            if data.get("errcode"):
                raise HTTPException(status_code=401, detail=f"微信登录失败: {data.get('errmsg')}")
            openid = data.get("openid")
            session_key = data.get("session_key")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"调用微信接口失败: {e}")
    else:
        # 开发态降级（仍需小程序端走授权流程）
        openid = f"dev_{payload.code}"
        session_key = "dev"

    if not openid:
        raise HTTPException(status_code=401, detail="无法获取 openid")

    res = await db.execute(select(User).where(User.openid == openid))
    user = res.scalar_one_or_none()
    if not user:
        user = User(
            username=f"wx_{openid[:10]}",
            password=get_password_hash("wechat_login"),
            nickname=payload.nickName or "微信用户",
            avatar=payload.avatarUrl or "https://picsum.photos/120/120?random=99",
            openid=openid,
            session_key=session_key,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        # 同步最新昵称头像
        if payload.nickName:
            user.nickname = payload.nickName
        if payload.avatarUrl:
            user.avatar = payload.avatarUrl
        user.session_key = session_key
        await db.commit()
        await db.refresh(user)

    return await _build_login_response(user)


@router.get("/me", response_model=UserSchema)
async def me(user: User = Depends(get_current_user)):
    return user


class ProfileUpdate(BaseModel):
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    phone: Optional[str] = None


@router.put("/me", response_model=UserSchema)
async def update_profile(
    payload: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(user, k, v)
    await db.commit()
    await db.refresh(user)
    return user