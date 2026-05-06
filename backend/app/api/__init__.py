from fastapi import APIRouter

api_router = APIRouter()

from . import courses, products, users, live, ai_test, orders, auth

# 添加各个模块的路由
api_router.include_router(courses.router)
api_router.include_router(products.router)
api_router.include_router(users.router)
api_router.include_router(live.router)
api_router.include_router(ai_test.router)
api_router.include_router(orders.router)
api_router.include_router(auth.router)

__all__ = ["api_router"]
