"""
Order placement logic.
Translates validated user input into Binance Futures API calls
and formats the responses for display.
"""

import logging
from decimal import Decimal
from typing import Any, Dict, Optional

from .client import BinanceFuturesClient

logger = logging.getLogger(__name__)


class OrderResult:
    """Structured representation of a placed order response."""

    def __init__(self, raw: Dict[str, Any]) -> None:
        self.raw = raw
        self.order_id: int = raw.get("orderId", 0)
        self.client_order_id: str = raw.get("clientOrderId", "")
        self.symbol: str = raw.get("symbol", "")
        self.side: str = raw.get("side", "")
        self.order_type: str = raw.get("type", "")
        self.status: str = raw.get("status", "")
        self.price: str = raw.get("price", "0")
        self.orig_qty: str = raw.get("origQty", "0")
        self.executed_qty: str = raw.get("executedQty", "0")
        self.avg_price: str = raw.get("avgPrice", "0")
        self.time_in_force: str = raw.get("timeInForce", "")
        self.update_time: int = raw.get("updateTime", 0)

    def summary(self) -> str:
        lines = [
            "─" * 52,
            f"  Order ID      : {self.order_id}",
            f"  Symbol        : {self.symbol}",
            f"  Side          : {self.side}",
            f"  Type          : {self.order_type}",
            f"  Status        : {self.status}",
            f"  Orig Qty      : {self.orig_qty}",
            f"  Executed Qty  : {self.executed_qty}",
            f"  Avg Price     : {self.avg_price}",
            f"  Limit Price   : {self.price}",
            f"  Time-in-Force : {self.time_in_force}",
            "─" * 52,
        ]
        return "\n".join(lines)


class OrderManager:
    """
    High-level order management layer.
    Accepts validated parameters, delegates to BinanceFuturesClient,
    and returns structured OrderResult objects.
    """

    def __init__(self, client: BinanceFuturesClient) -> None:
        self._client = client

    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
    ) -> OrderResult:
        """Place a MARKET order."""
        logger.info(
            "Market order request | symbol=%s side=%s qty=%s",
            symbol, side, quantity,
        )
        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": str(quantity),
        }
        raw = self._client.place_order(**params)
        result = OrderResult(raw)
        logger.info("Market order placed | orderId=%s status=%s", result.order_id, result.status)
        return result

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Decimal,
        time_in_force: str = "GTC",
    ) -> OrderResult:
        """Place a LIMIT order."""
        logger.info(
            "Limit order request | symbol=%s side=%s qty=%s price=%s tif=%s",
            symbol, side, quantity, price, time_in_force,
        )
        params = {
            "symbol": symbol,
            "side": side,
            "type": "LIMIT",
            "quantity": str(quantity),
            "price": str(price),
            "timeInForce": time_in_force,
        }
        raw = self._client.place_order(**params)
        result = OrderResult(raw)
        logger.info("Limit order placed | orderId=%s status=%s", result.order_id, result.status)
        return result

    def place_stop_market_order(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        stop_price: Decimal,
    ) -> OrderResult:
        """Place a STOP_MARKET order (bonus order type)."""
        logger.info(
            "Stop-Market order request | symbol=%s side=%s qty=%s stopPrice=%s",
            symbol, side, quantity, stop_price,
        )
        params = {
            "symbol": symbol,
            "side": side,
            "type": "STOP_MARKET",
            "quantity": str(quantity),
            "stopPrice": str(stop_price),
        }
        raw = self._client.place_order(**params)
        result = OrderResult(raw)
        logger.info(
            "Stop-Market order placed | orderId=%s status=%s", result.order_id, result.status
        )
        return result
