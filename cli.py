#!/usr/bin/env python3
"""
cli.py – Command-line interface for the Binance Futures Testnet Trading Bot.

Usage examples:
  python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
  python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 60000
  python cli.py place --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 58000
  python cli.py account
"""

import argparse
import json
import logging
import os
import sys
from decimal import Decimal

from bot.client import BinanceFuturesClient, BinanceAPIError, NetworkError
from bot.logging_config import setup_logging
from bot.orders import OrderManager
from bot.validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    validate_stop_price,
)

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _print_section(title: str, content: str) -> None:
    print(f"\n{'━' * 54}")
    print(f"  {title}")
    print(f"{'━' * 54}")
    print(content)


def _get_credentials() -> tuple[str, str]:
    """Read API key and secret from environment variables."""
    api_key = os.getenv("BINANCE_TESTNET_API_KEY", "")
    api_secret = os.getenv("BINANCE_TESTNET_API_SECRET", "")
    if not api_key or not api_secret:
        print(
            "\n[ERROR] Environment variables BINANCE_TESTNET_API_KEY and "
            "BINANCE_TESTNET_API_SECRET must be set.\n"
            "  export BINANCE_TESTNET_API_KEY=your_key\n"
            "  export BINANCE_TESTNET_API_SECRET=your_secret\n"
        )
        sys.exit(1)
    return api_key, api_secret


# ──────────────────────────────────────────────────────────────────────────────
# Sub-command handlers
# ──────────────────────────────────────────────────────────────────────────────

def cmd_place(args: argparse.Namespace) -> None:
    """Validate inputs, place order, display result."""
    # ── Validate ──────────────────────────────────────────────────────────────
    try:
        symbol = validate_symbol(args.symbol)
        side = validate_side(args.side)
        order_type = validate_order_type(args.type)
        quantity = validate_quantity(args.quantity)
        price = validate_price(args.price, order_type)
        stop_price = validate_stop_price(args.stop_price, order_type)
    except ValueError as exc:
        print(f"\n[VALIDATION ERROR] {exc}\n")
        logger.warning("Validation failed: %s", exc)
        sys.exit(2)

    # ── Request summary ───────────────────────────────────────────────────────
    summary_lines = [
        f"  Symbol    : {symbol}",
        f"  Side      : {side}",
        f"  Type      : {order_type}",
        f"  Quantity  : {quantity}",
    ]
    if price:
        summary_lines.append(f"  Price     : {price}")
    if stop_price:
        summary_lines.append(f"  Stop Price: {stop_price}")
    _print_section("ORDER REQUEST", "\n".join(summary_lines))

    # ── Build client & manager ────────────────────────────────────────────────
    api_key, api_secret = _get_credentials()
    client = BinanceFuturesClient(api_key=api_key, api_secret=api_secret)
    manager = OrderManager(client)

    # ── Place order ───────────────────────────────────────────────────────────
    try:
        if order_type == "MARKET":
            result = manager.place_market_order(symbol, side, quantity)
        elif order_type == "LIMIT":
            tif = (args.time_in_force or "GTC").upper()
            result = manager.place_limit_order(symbol, side, quantity, price, tif)
        elif order_type == "STOP_MARKET":
            result = manager.place_stop_market_order(symbol, side, quantity, stop_price)
        else:
            print(f"[ERROR] Unhandled order type: {order_type}")
            sys.exit(1)

    except BinanceAPIError as exc:
        print(f"\n[API ERROR] {exc}\n")
        logger.error("API error placing order: %s", exc)
        sys.exit(1)
    except NetworkError as exc:
        print(f"\n[NETWORK ERROR] {exc}\n")
        logger.error("Network error placing order: %s", exc)
        sys.exit(1)
    except Exception as exc:
        print(f"\n[UNEXPECTED ERROR] {exc}\n")
        logger.exception("Unexpected error placing order")
        sys.exit(1)

    # ── Display result ────────────────────────────────────────────────────────
    _print_section("ORDER RESPONSE", result.summary())
    print(f"\n  ✅  Order placed successfully! (orderId={result.order_id})\n")

    if args.json:
        print("── Raw JSON ──")
        print(json.dumps(result.raw, indent=2))


def cmd_account(args: argparse.Namespace) -> None:
    """Fetch and display account information."""
    api_key, api_secret = _get_credentials()
    client = BinanceFuturesClient(api_key=api_key, api_secret=api_secret)
    try:
        data = client.get_account()
    except (BinanceAPIError, NetworkError) as exc:
        print(f"\n[ERROR] {exc}\n")
        sys.exit(1)

    assets = [a for a in data.get("assets", []) if float(a.get("walletBalance", 0)) > 0]
    lines = ["  Non-zero balances:"]
    for a in assets:
        lines.append(f"    {a['asset']:<8} wallet={a['walletBalance']}  unrealisedPnl={a['unrealizedProfit']}")
    if not assets:
        lines.append("    (no funded assets found)")
    _print_section("ACCOUNT INFO", "\n".join(lines))


# ──────────────────────────────────────────────────────────────────────────────
# Argument parser
# ──────────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Market buy
  python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

  # Limit sell
  python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 100000

  # Stop-market sell (bonus)
  python cli.py place --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 58000

  # Account balance
  python cli.py account
        """,
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # ── place ─────────────────────────────────────────────────────────────────
    place_p = subparsers.add_parser("place", help="Place a new futures order")
    place_p.add_argument("--symbol",     required=True, help="Trading pair, e.g. BTCUSDT")
    place_p.add_argument("--side",       required=True, help="BUY or SELL")
    place_p.add_argument("--type",       required=True, dest="type", help="MARKET, LIMIT, or STOP_MARKET")
    place_p.add_argument("--quantity",   required=True, help="Order quantity")
    place_p.add_argument("--price",      default=None,  help="Limit price (required for LIMIT)")
    place_p.add_argument("--stop-price", default=None,  dest="stop_price",
                         help="Stop price (required for STOP_MARKET)")
    place_p.add_argument("--time-in-force", default="GTC", dest="time_in_force",
                         help="GTC (default), IOC, FOK – applies to LIMIT orders")
    place_p.add_argument("--json", action="store_true", help="Also print raw JSON response")
    place_p.set_defaults(func=cmd_place)

    # ── account ───────────────────────────────────────────────────────────────
    acct_p = subparsers.add_parser("account", help="Show futures account balances")
    acct_p.set_defaults(func=cmd_account)

    return parser


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    setup_logging(args.log_level)
    logger.info("CLI invoked | command=%s args=%s", args.command, vars(args))

    args.func(args)


if __name__ == "__main__":
    main()
