from fastapi import APIRouter

from app.api.v1.endpoints import (
    addresses, auth, branches, cart, categories, coupons, custom_cakes, health, inventory, notifications,
    orders, products, reviews,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(cart.router, prefix="/cart", tags=["cart"])
api_router.include_router(addresses.router, prefix="/addresses", tags=["addresses"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(branches.router, prefix="/branches", tags=["branches"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(coupons.router, prefix="/coupons", tags=["coupons"])
api_router.include_router(custom_cakes.router, prefix="/custom-cakes", tags=["custom cakes"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])

# Future modules will be wired in here, e.g.:
# api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
# api_router.include_router(pos.router, prefix="/pos", tags=["pos"])
# api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
