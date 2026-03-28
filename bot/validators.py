"""
Input validation for trading bot CLI arguments.
All validation errors raise ValueError with a descriptive message.
"""

from decimal import Decimal, InvalidOperation
from typing import Optional


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


def validate_symbol(symbol: str) -> str:
    """Validate and normalise the trading pair symbol."""
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("Symbol must not be empty.")
    if len(symbol) < 4:
        raise ValueError(f"Symbol '{symbol}' looks too short. Example: BTCUSDT")
    if not symbol.isalnum():
        raise ValueError(f"Symbol '{symbol}' must be alphanumeric (e.g. BTCUSDT).")
    return symbol


def validate_side(side: str) -> str:
    """Validate order side (BUY / SELL)."""
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}"
        )
    return side


def validate_order_type(order_type: str) -> str:
    """Validate order type (MARKET / LIMIT / STOP_MARKET)."""
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. "
            f"Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}"
        )
    return order_type


def validate_quantity(quantity: str) -> Decimal:
    """Validate and parse quantity as a positive Decimal."""
    try:
        qty = Decimal(str(quantity))
    except InvalidOperation:
        raise ValueError(f"Invalid quantity '{quantity}'. Must be a positive number.")
    if qty <= 0:
        raise ValueError(f"Quantity must be greater than zero, got {qty}.")
    return qty


def validate_price(price: Optional[str], order_type: str) -> Optional[Decimal]:
    """
    Validate price:
    - Required for LIMIT orders.
    - Required for STOP_MARKET (used as stopPrice).
    - Ignored for MARKET orders.
    """
    if order_type in ("LIMIT", "STOP_MARKET"):
        if price is None:
            raise ValueError(f"--price is required for {order_type} orders.")
        try:
            p = Decimal(str(price))
        except InvalidOperation:
            raise ValueError(f"Invalid price '{price}'. Must be a positive number.")
        if p <= 0:
            raise ValueError(f"Price must be greater than zero, got {p}.")
        return p
    # MARKET order – price is irrelevant
    if price is not None:
        # Warn but don't error; price will simply be ignored
        pass
    return None


def validate_stop_price(stop_price: Optional[str], order_type: str) -> Optional[Decimal]:
    """Validate stopPrice for STOP_MARKET orders."""
    if order_type == "STOP_MARKET":
        if stop_price is None:
            raise ValueError("--stop-price is required for STOP_MARKET orders.")
        try:
            sp = Decimal(str(stop_price))
        except InvalidOperation:
            raise ValueError(f"Invalid stop price '{stop_price}'. Must be a positive number.")
        if sp <= 0:
            raise ValueError(f"Stop price must be greater than zero, got {sp}.")
        return sp
    return None
