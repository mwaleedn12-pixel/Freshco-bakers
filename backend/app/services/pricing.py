from decimal import ROUND_HALF_UP, Decimal

from app.models.catalog import Product

TWO_PLACES = Decimal("0.01")


def q2(value) -> Decimal:
    return Decimal(str(value)).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def effective_price(product: Product) -> Decimal:
    """Price the customer actually pays: sale_price when set, else price. Always decided by the server."""
    if product.sale_price is not None and Decimal(str(product.sale_price)) > 0:
        return q2(product.sale_price)
    return q2(product.price)
