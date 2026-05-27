from .session import async_engine, AsyncSessionLocal, Base

# 懒加载 init_db，避免循环导入：
# init_db 依赖 models，而 models 依赖 Base（来自 session），
# 如果在模块顶层导入 init_db，会触发 models -> database -> init_db -> models 的循环
def init_db(*args, **kwargs):
    from .init_db import _init_db
    return _init_db(*args, **kwargs)

__all__ = ["async_engine", "AsyncSessionLocal", "Base", "init_db"]
