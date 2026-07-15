from fastapi import APIRouter

api_router = APIRouter()

from . import courses, products, users, live, ai_test, orders, auth, questions, me, uploads, address, cart

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(courses.router)
api_router.include_router(products.router)
api_router.include_router(live.router)
api_router.include_router(ai_test.router)
api_router.include_router(orders.router)
api_router.include_router(questions.router)
api_router.include_router(me.router)
api_router.include_router(uploads.router)
api_router.include_router(address.router)
api_router.include_router(cart.router)

__all__ = ["api_router"]