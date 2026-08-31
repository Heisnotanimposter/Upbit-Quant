import time
import base64
import hashlib
import hmac
import urllib.parse
import requests
import jwt
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger("BithumbClient")

class BithumbClient:
    """
    Robust REST API client for Bithumb (KRW market).
    Handles JWT authentication, rate limiting, and backoff retries for high availability.
    """
    BASE_URL = "https://api.bithumb.com"

    def __init__(self, access_key: str, secret_key: str, dry_run: bool = True):
        self.access_key = access_key
        self.secret_key = secret_key
        self.dry_run = dry_run
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "BithumbQuantEngine/1.0"
        })

    def _generate_jwt_token(self, params: Dict[str, Any] = None) -> str:
        """Generates JWT token for Bithumb private endpoints."""
        nonce = str(int(time.time() * 1000))
        payload = {
            "access_key": self.access_key,
            "nonce": nonce,
            "timestamp": nonce
        }

        if params:
            query_string = urllib.parse.urlencode(params)
            query_hash = hashlib.sha512(query_string.encode('utf-8')).hexdigest()
            payload["query_hash"] = query_hash
            payload["query_hash_alg"] = "SHA512"

        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        return f"Bearer {token}"

    def _request_with_retry(self, method: str, endpoint: str, params: Dict[str, Any] = None, data: Dict[str, Any] = None, is_private: bool = False, max_retries: int = 5) -> Dict[str, Any]:
        """
        Executes HTTP request with exponential backoff retry for network resiliency.
        Automatically handles Bithumb maintenance (502/503) and rate limits (429).
        """
        url = f"{self.BASE_URL}{endpoint}"
        delay = 1.0

        for attempt in range(max_retries):
            try:
                headers = {}
                if is_private:
                    if not self.access_key or not self.secret_key:
                        raise ValueError("Bithumb API keys are not set.")
                    payload_for_hash = data if method == "POST" else params
                    headers["Authorization"] = self._generate_jwt_token(payload_for_hash)

                if method == "GET":
                    response = self.session.get(url, params=params, headers=headers, timeout=10)
                elif method == "POST":
                    response = self.session.post(url, data=data, headers=headers, timeout=10)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Success
                if response.status_code == 200:
                    res_json = response.json()
                    status = res_json.get("status")
                    if status == "0000":
                        return res_json
                    elif status == "5600": # Bithumb Maintenance
                        logger.warning(f"Bithumb maintenance in progress (Attempt {attempt+1}/{max_retries}). Retrying in {delay}s...")
                    else:
                        logger.error(f"Bithumb API error response: {res_json}")
                        return res_json

                elif response.status_code in (429, 500, 502, 503, 504):
                    logger.warning(f"Bithumb server returned HTTP {response.status_code}. Retrying in {delay:.1f}s...")
                else:
                    logger.error(f"HTTP {response.status_code}: {response.text}")
                    response.raise_for_status()

            except (requests.exceptions.RequestException, jwt.PyJWTError) as e:
                logger.warning(f"Network / Auth exception on {endpoint}: {e}. Retrying in {delay:.1f}s...")

            time.sleep(delay)
            delay *= 2.0  # Exponential backoff

        logger.critical(f"Failed Bithumb API request to {endpoint} after {max_retries} retries.")
        return {"status": "9999", "message": "Max retries exceeded"}

    # --- PUBLIC MARKET DATA ENDPOINTS ---

    def get_ticker(self, order_currency: str, payment_currency: str = "KRW") -> Optional[Dict[str, Any]]:
        """Gets current ticker data for a crypto symbol."""
        symbol = f"{order_currency}_{payment_currency}"
        res = self._request_with_retry("GET", f"/public/ticker/{symbol}")
        if res.get("status") == "0000":
            return res.get("data", {})
        return None

    def get_candlestick(self, order_currency: str, payment_currency: str = "KRW", interval: str = "24h") -> Optional[List[List[Any]]]:
        """
        Gets OHLCV Candlestick data.
        interval: 1m, 3m, 5m, 10m, 30m, 1h, 6h, 12h, 24h
        Return structure per candle: [Timestamp, Open, Close, High, Low, Volume]
        """
        symbol = f"{order_currency}_{payment_currency}"
        res = self._request_with_retry("GET", f"/public/candlestick/{symbol}/{interval}")
        if res.get("status") == "0000":
            return res.get("data", [])
        return None

    # --- PRIVATE TRADING & ACCOUNT ENDPOINTS ---

    def get_balance(self, currency: str = "ALL") -> Dict[str, Any]:
        """Gets account balance for KRW and coin holdings."""
        if self.dry_run:
            # Paper trading mock balance
            return {
                "status": "0000",
                "data": {
                    "total_krw": "10000000",
                    "in_use_krw": "0",
                    "available_krw": "10000000",
                    "total_btc": "0.0",
                    "available_btc": "0.0",
                    "total_eth": "0.0",
                    "available_eth": "0.0"
                }
            }
        data = {"currency": currency}
        return self._request_with_retry("POST", "/info/balance", data=data, is_private=True)

    def place_market_buy(self, order_currency: str, total_krw: float, payment_currency: str = "KRW") -> Dict[str, Any]:
        """Places a market buy order for specified KRW amount."""
        if self.dry_run:
            logger.info(f"[DRY_RUN PAPER BUY] Symbol: {order_currency}_{payment_currency}, Amount: {total_krw:,.0f} KRW")
            return {
                "status": "0000",
                "order_id": f"PAPER_BUY_{int(time.time()*1000)}",
                "data": [{"cont_id": "PAPER_1", "price": "100000000", "units": str(total_krw / 100000000), "fee": "0"}]
            }

        data = {
            "order_currency": order_currency,
            "payment_currency": payment_currency,
            "units": str(total_krw),  # Bithumb market buy takes KRW total as units
            "currency": order_currency
        }
        return self._request_with_retry("POST", "/trade/market_buy", data=data, is_private=True)

    def place_market_sell(self, order_currency: str, units: float, payment_currency: str = "KRW") -> Dict[str, Any]:
        """Places a market sell order for specified coin quantity."""
        if self.dry_run:
            logger.info(f"[DRY_RUN PAPER SELL] Symbol: {order_currency}_{payment_currency}, Units: {units}")
            return {
                "status": "0000",
                "order_id": f"PAPER_SELL_{int(time.time()*1000)}",
                "data": [{"cont_id": "PAPER_2", "price": "100000000", "units": str(units), "fee": "0"}]
            }

        data = {
            "order_currency": order_currency,
            "payment_currency": payment_currency,
            "units": f"{units:.8f}",
            "currency": order_currency
        }
        return self._request_with_retry("POST", "/trade/market_sell", data=data, is_private=True)
