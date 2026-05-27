import socket

s = socket.socket()
s.settimeout(2)
try:
    s.connect(("127.0.0.1", 8000))
    print("connected (端口活的，有进程在响应)")
    s.close()
except ConnectionRefusedError:
    print("refused (幽灵 socket - 监听存在但没人 accept)")
except Exception as e:
    print(f"other: {type(e).__name__}: {e}")