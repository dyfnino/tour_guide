"""试探 8000 端口在不同地址下的可绑定性。"""
import socket

for host in ("0.0.0.0", "127.0.0.1", "::"):
    try:
        family = socket.AF_INET6 if host == "::" else socket.AF_INET
        s = socket.socket(family, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, 8000))
        s.listen(1)
        print(f"[OK] {host}:8000 可绑定")
        s.close()
    except OSError as e:
        print(f"[FAIL] {host}:8000 绑定失败: {e}")