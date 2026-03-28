# 🤖 Binance Futures Testnet Trading Bot

A clean, production-style Python CLI trading bot for Binance Futures Testnet (USDT-M).  
Supports **MARKET**, **LIMIT**, and **STOP_MARKET** orders with structured logging, input validation, and proper error handling.

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST client (signing, retries, HTTP)
│   ├── orders.py          # Order placement logic + OrderResult model
│   ├── validators.py      # CLI input validation
│   └── logging_config.py  # Rotating file + console logging setup
├── cli.py                 # CLI entry point (argparse)
├── logs/
│   └── trading_bot.log    # Auto-created on first run
├── README.md
└── requirements.txt
```

---

## Setup

### 1. Get Testnet Credentials

1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com) and log in (GitHub auth supported).
2. Navigate to **API Key** section and generate a key pair.
3. Copy your **API Key** and **Secret Key**.

### 2. Install Dependencies

```bash
# Python 3.10+ recommended
pip install -r requirements.txt
```

### 3. Set Environment Variables

```bash
export BINANCE_TESTNET_API_KEY="your_api_key_here"
export BINANCE_TESTNET_API_SECRET="your_api_secret_here"
```

> On Windows (PowerShell):
> ```powershell
> $env:BINANCE_TESTNET_API_KEY = "your_api_key_here"
> $env:BINANCE_TESTNET_API_SECRET = "your_api_secret_here"
> ```

---

## How to Run

### Place a MARKET order

```bash
# Buy 0.001 BTC at market price
python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# Sell 0.01 ETH at market price
python cli.py place --symbol ETHUSDT --side SELL --type MARKET --quantity 0.01
```

### Place a LIMIT order

```bash
# Sell 0.001 BTC when price reaches $86,000 (GTC)
python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 86000

# Buy 0.001 BTC with IOC (Immediate-or-Cancel)
python cli.py place --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 80000 --time-in-force IOC
```

### Place a STOP_MARKET order *(bonus)*

```bash
# Stop-loss sell trigger at $82,000
python cli.py place --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 82000
```

### View account balances

```bash
python cli.py account
```

### Increase log verbosity (DEBUG shows full request/response)

```bash
python cli.py --log-level DEBUG place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Print raw JSON response

```bash
python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001 --json
```

---

## Example Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ORDER REQUEST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Symbol    : BTCUSDT
  Side      : BUY
  Type      : MARKET
  Quantity  : 0.001

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ORDER RESPONSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
────────────────────────────────────────────────────
  Order ID      : 4074043506
  Symbol        : BTCUSDT
  Side          : BUY
  Type          : MARKET
  Status        : FILLED
  Orig Qty      : 0.001
  Executed Qty  : 0.001
  Avg Price     : 84123.50
  Limit Price   : 0
  Time-in-Force : GTC
────────────────────────────────────────────────────

  ✅  Order placed successfully! (orderId=4074043506)
```

---

## Logging

Logs are written to `logs/trading_bot.log` (auto-created).

- **File handler**: All levels ≥ `--log-level` (default `INFO`)
- **Console**: Warnings and above only (to keep terminal clean)
- Rotating: max 5 MB per file, 5 backups kept

Log format:
```
2025-03-28 10:12:01 | INFO     | bot.orders | Market order placed | orderId=4074043506 status=FILLED
```

---

## CLI Reference

```
usage: trading_bot place [-h] --symbol SYMBOL --side SIDE --type TYPE
                         --quantity QUANTITY [--price PRICE]
                         [--stop-price STOP_PRICE]
                         [--time-in-force TIME_IN_FORCE] [--json]

options:
  --symbol              Trading pair (e.g. BTCUSDT)
  --side                BUY or SELL
  --type                MARKET, LIMIT, or STOP_MARKET
  --quantity            Order quantity
  --price               Limit price (required for LIMIT orders)
  --stop-price          Stop trigger price (required for STOP_MARKET)
  --time-in-force       GTC (default), IOC, FOK
  --json                Also print the raw JSON API response
  --log-level           DEBUG | INFO | WARNING | ERROR  (default: INFO)
```

---

## Assumptions

- **Testnet only**: The base URL is hardcoded to `https://testnet.binancefuture.com`. Swap to `https://fapi.binance.com` for production (with real credentials).
- **One-way mode**: Orders are placed assuming default position mode. Hedge-mode (`positionSide`) is not used.
- **Quantity precision**: The user is responsible for providing quantities that satisfy Binance's LOT_SIZE filter for the chosen symbol (e.g., BTCUSDT minimum is 0.001).
- **No order book checks**: The bot does not pre-validate prices against the order book; Binance will reject orders that violate price filters.
- Credentials are read from environment variables — never hard-coded.

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Missing required arg | argparse exits with usage message |
| Invalid symbol / side / type | Validation error printed, exit code 2 |
| Missing price for LIMIT | Validation error printed, exit code 2 |
| Binance API error (e.g. -1121) | Error code + message printed, logged, exit code 1 |
| Network timeout / connection failure | Network error printed, logged, exit code 1 |
| Unexpected exception | Full traceback logged to file, generic message printed |
