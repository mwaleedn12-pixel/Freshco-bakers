from fastapi import APIRouter

from app.api.v1.endpoints import auth, health

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Future modules will be wired in here, e.g.:
# from app.api.v1.endpoints import products, orders, pos
# api_router.include_router(products.router, prefix="/products", tags=["products"])
# api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
# api_router.include_router(pos.router, prefix="/pos", tags=["pos"])
