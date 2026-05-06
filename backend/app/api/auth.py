from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import requests
import json
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

from ..database.session import get_db
from ..models.user import User
from ..schemas.user import WechatLogin, LoginResponse, UserCreate

# 加载环境变量
load_dotenv()

router = APIRouter(prefix="/auth", tags=["authentication"])

# 微信小程序配置
WECHAT_APPID = os.getenv("WECHAT_APPID", "your_appid")
WECHAT_SECRET = os.getenv("WECHAT_SECRET", "your_secret")
WECHAT_LOGIN_URL = "https://api.weixin.qq.com/sns/jscode2session"

# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 生成JWT令牌
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 验证密码
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# 获取密码哈希
def get_password_hash(password):
    return pwd_context.hash(password)

# 微信登录
@router.post("/wechat", response_model=LoginResponse)
async def wechat_login(
    login_data: WechatLogin,
    db: AsyncSession = Depends(get_db)
):
    try:
        # 调用微信API获取openid和session_key
        response = requests.get(
            WECHAT_LOGIN_URL,
            params={
                "appid": WECHAT_APPID,
                "secret": WECHAT_SECRET,
                "js_code": login_data.code,
                "grant_type": "authorization_code"
            }
        )
        
        result = response.json()
        print("Wechat login result:", result)
        
        if "errcode" in result and result["errcode"] != 0:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Wechat login failed: {result['errmsg']}"
            )
        
        openid = result.get("openid")
        session_key = result.get("session_key")
        
        if not openid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to get openid from wechat"
            )
        
        # 检查用户是否已存在
        result = await db.execute(select(User).where(User.openid == openid))
        user = result.scalar_one_or_none()
        
        if not user:
            # 创建新用户
            username = f"wechat_{openid[:8]}"
            password = get_password_hash("wechat_login")  # 微信登录用户的默认密码
            nickname = "微信用户"
            
            user = User(
                username=username,
                password=password,
                nickname=nickname,
                openid=openid,
                session_key=session_key
            )
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            # 更新现有用户的session_key
            user.session_key = session_key
            await db.commit()
            await db.refresh(user)
        
        # 生成访问令牌
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        return LoginResponse(access_token=access_token, user=user)
        
    except Exception as e:
        print(f"Wechat login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process wechat login"
        )
