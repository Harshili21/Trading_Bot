"""
Binance Futures Testnet REST client.
Handles authentication (HMAC-SHA256), request signing, and HTTP communication.
All requests and responses are logged at DEBUG level.
"""

import hashlib
import hmac
import logging
import time
import urllib.parse
from typing import Any, Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

TESTNET_BASE_URL = "https://testnet.binancefuture.com"
DEFAULT_TIMEOUT = 10  # seconds
MAX_RETRIES = 3


class BinanceAPIError(Exception):
    """Raised when Binance returns a non-2xx response or error payload."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")


class NetworkError(Exception):
    """Raised on network / connection failures."""


class BinanceFuturesClient:
    """
    Thin wrapper around Binance Futures Testnet REST API.

    Parameters
    ----------
    api_key : str
        Your Binance Futures Testnet API key.
    api_secret : str
        Your Binance Futures Testnet API secret.
    base_url : str
        Base URL (defaults to testnet).
    timeout : int
        Request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = TESTNET_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        if not api_key or not api_secret:
            raise ValueError("api_key and api_secret must not be empty.")
        self._api_key = api_key
        self._api_secret = api_secret
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = self._build_session()
        logger.info("BinanceFuturesClient initialised (base_url=%s)", self._base_url)

    # ------------------------------------------------------------------
    # Session construction
    # ------------------------------------------------------------------

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "X-MBX-APIKEY": self._api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        retry = Retry(
            total=MAX_RETRIES,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    # ------------------------------------------------------------------
    # Signing helpers
    # ------------------------------------------------------------------

    def _sign(self, params: Dict[str, Any]) -> str:
        """Return HMAC-SHA256 signature for the query-string of *params*."""
        query_string = urllib.parse.urlencode(params)
        return hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _signed_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Append timestamp and signature to *params* (mutates a copy)."""
        p = dict(params)
        p["timestamp"] = int(time.time() * 1000)
        p["signature"] = self._sign(p)
        return p

    # ------------------------------------------------------------------
    # Low-level HTTP methods
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
    ) -> Any:
        url = f"{self._base_url}{path}"
        p = params or {}
        if signed:
            p = self._signed_params(p)

        logger.debug("→ %s %s | params=%s", method.upper(), url, p)

        try:
            resp = self._session.request(
                method=method,
                url=url,
                params=p if method.upper() == "GET" else None,
                data=p if method.upper() == "POST" else None,
                timeout=self._timeout,
            )
        except requests.exceptions.ConnectionError as exc:
            logger.error("Network connection error: %s", exc)
            raise NetworkError(f"Connection error: {exc}") from exc
        except requests.exceptions.Timeout as exc:
            logger.error("Request timed out after %ss", self._timeout)
            raise NetworkError(f"Request timed out: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            logger.error("Unexpected request error: %s", exc)
            raise NetworkError(f"Request error: {exc}") from exc

        logger.debug("← HTTP %s | %s", resp.status_code, resp.text[:500])

        try:
            data = resp.json()
        except ValueError:
            logger.error("Non-JSON response: %s", resp.text[:200])
            raise BinanceAPIError(-1, f"Non-JSON response: {resp.text[:200]}")

        if not resp.ok or (isinstance(data, dict) and "code" in data and data["code"] < 0):
            code = data.get("code", resp.status_code) if isinstance(data, dict) else resp.status_code
            msg = data.get("msg", resp.text) if isinstance(data, dict) else resp.text
            logger.error("API error %s: %s", code, msg)
            raise BinanceAPIError(code, msg)

        return data

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_server_time(self) -> Dict[str, Any]:
        """Fetch server time – useful for connectivity checks."""
        return self._request("GET", "/fapi/v1/time")

    def get_exchange_info(self) -> Dict[str, Any]:
        """Return exchange trading rules and symbol info."""
        return self._request("GET", "/fapi/v1/exchangeInfo")

    def get_account(self) -> Dict[str, Any]:
        """Return futures account information (signed)."""
        return self._request("GET", "/fapi/v2/account", signed=True)

    def place_order(self, **order_params: Any) -> Dict[str, Any]:
        """
        Place a new order on Binance Futures.

        Keyword args are forwarded directly as POST params.
        Required keys: symbol, side, type, quantity (and price / stopPrice as needed).
        """
        logger.info("Placing order: %s", order_params)
        result = self._request("POST", "/fapi/v1/order", params=order_params, signed=True)
        logger.info("Order accepted: orderId=%s status=%s", result.get("orderId"), result.get("status"))
        return result

    def get_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Query a specific order by ID."""
        return self._request(
            "GET",
            "/fapi/v1/order",
            params={"symbol": symbol, "orderId": order_id},
            signed=True,
        )

    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an open order."""
        return self._request(
            "DELETE",
            "/fapi/v1/order",
            params={"symbol": symbol, "orderId": order_id},
            signed=True,
        )
