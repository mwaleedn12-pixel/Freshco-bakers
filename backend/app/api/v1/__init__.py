from fastapi import APIRouter

from app.api.v1.endpoints import addresses, auth, cart, categories, health, orders, products

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(cart.router, prefix="/cart", tags=["cart"])
api_router.include_router(addresses.router, prefix="/addresses", tags=["addresses"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])

# Future modules will be wired in here, e.g.:
# api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
# api_router.include_router(pos.router, prefix="/pos", tags=["pos"])
