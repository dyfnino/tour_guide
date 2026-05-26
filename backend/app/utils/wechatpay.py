"""
微信支付 v3 服务封装（小程序 JSAPI）。

依赖：wechatpayv3
docs:  https://github.com/minibear2021/wechatpayv3

通过 .env 配置：
- WX_PAY_MOCK: 1 时所有支付走 Mock，立刻返回 paid（仅本地联调用）
- WX_PAY_APPID / WX_PAY_MCHID / WX_PAY_APIV3_KEY / WX_PAY_CERT_SERIAL_NO
- WX_PAY_PRIVATE_KEY_PATH (apiclient_key.pem)
- WX_PAY_CERT_DIR        (微信平台证书目录，可不存在，SDK 会自动下载)
- WX_PAY_NOTIFY_URL      (回调地址)
"""
import os
import time
import uuid
import json
import base64
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

# wechatpayv3 是同步 SDK，这里以同步调用方式接入
try:
    from wechatpayv3 import WeChatPay, WeChatPayType
except Exception:  # pragma: no cover
    WeChatPay = None
    WeChatPayType = None


def _bool(env: str, default: bool = False) -> bool:
    v = os.getenv(env, "").strip().lower()
    if not v:
        return default
    return v in ("1", "true", "yes", "y")


def is_mock() -> bool:
    return _bool("WX_PAY_MOCK", True)


def get_appid() -> str:
    return os.getenv("WX_PAY_APPID", "").strip()


def _backend_root() -> Path:
    # backend/ 目录（main.py 同级）
    return Path(__file__).resolve().parents[2]


def _resolve(p: str) -> Path:
    path = Path(p)
    if not path.is_absolute():
        path = _backend_root() / path
    return path


_client: Optional["WeChatPay"] = None


def get_client() -> "WeChatPay":
    """构造（或复用）微信支付客户端。Mock 模式返回 None。"""
    global _client
    if is_mock():
        return None
    if _client is not None:
        return _client
    if WeChatPay is None:
        raise RuntimeError("wechatpayv3 未安装，请在 requirements.txt 中加入并安装")

    private_key_path = _resolve(os.getenv("WX_PAY_PRIVATE_KEY_PATH", "certs/apiclient_key.pem"))
    cert_dir = _resolve(os.getenv("WX_PAY_CERT_DIR", "certs/wx_platform"))
    cert_dir.mkdir(parents=True, exist_ok=True)

    if not private_key_path.exists():
        raise RuntimeError(f"商户私钥不存在: {private_key_path}")

    with open(private_key_path, "r", encoding="utf-8") as f:
        private_key = f.read()

    _client = WeChatPay(
        wechatpay_type=WeChatPayType.MINIPROG,
        mchid=os.getenv("WX_PAY_MCHID", "").strip(),
        private_key=private_key,
        cert_serial_no=os.getenv("WX_PAY_CERT_SERIAL_NO", "").strip(),
        apiv3_key=os.getenv("WX_PAY_APIV3_KEY", "").strip(),
        appid=get_appid(),
        notify_url=os.getenv("WX_PAY_NOTIFY_URL", "").strip(),
        cert_dir=str(cert_dir),
    )
    return _client


def jsapi_pay(*, out_trade_no: str, amount_fen: int, description: str, openid: str) -> Dict[str, Any]:
    """
    发起 JSAPI 下单，返回前端 wx.requestPayment 所需参数。
    Mock 模式直接造一组占位参数（前端看到的是模拟收银台）。
    """
    if is_mock():
        ts = str(int(time.time()))
        nonce = uuid.uuid4().hex
        return {
            "mock": True,
            "timeStamp": ts,
            "nonceStr": nonce,
            "package": "prepay_id=mock_" + uuid.uuid4().hex[:20],
            "signType": "RSA",
            "paySign": "MOCK_SIGN",
            "prepay_id": "mock_" + uuid.uuid4().hex[:20],
        }

    client = get_client()
    code, message = client.pay(
        description=description,
        out_trade_no=out_trade_no,
        amount={"total": amount_fen, "currency": "CNY"},
        payer={"openid": openid},
    )
    if code != 200:
        raise RuntimeError(f"微信下单失败: {code} {message}")
    data = json.loads(message)
    prepay_id = data.get("prepay_id")
    if not prepay_id:
        raise RuntimeError(f"微信下单返回缺少 prepay_id: {data}")

    # 计算 paySign
    timestamp = str(int(time.time()))
    nonce_str = uuid.uuid4().hex
    package = f"prepay_id={prepay_id}"
    sign_str = f"{get_appid()}\n{timestamp}\n{nonce_str}\n{package}\n"
    pay_sign = client.sign(sign_str)
    return {
        "mock": False,
        "timeStamp": timestamp,
        "nonceStr": nonce_str,
        "package": package,
        "signType": "RSA",
        "paySign": pay_sign,
        "prepay_id": prepay_id,
    }


def parse_notify(headers: Dict[str, str], body: bytes) -> Optional[Dict[str, Any]]:
    """
    解析微信支付回调；Mock 模式直接把 body 当 JSON 返回（约定字段：out_trade_no、transaction_id）。
    返回成功后的资源字典，失败返回 None。
    """
    if is_mock():
        try:
            return json.loads(body.decode("utf-8"))
        except Exception:
            return None

    client = get_client()
    # wechatpayv3 提供 callback 解析
    result = client.callback(headers=headers, body=body)
    if not result:
        return None
    if result.get("event_type") != "TRANSACTION.SUCCESS":
        return None
    resource = result.get("resource") or {}
    # 已经是解密后的 dict
    return resource


def query_by_out_trade_no(out_trade_no: str) -> Optional[Dict[str, Any]]:
    """主动查询订单状态。"""
    if is_mock():
        return None
    client = get_client()
    code, message = client.query(out_trade_no=out_trade_no)
    if code != 200:
        return None
    try:
        return json.loads(message)
    except Exception:
        return None