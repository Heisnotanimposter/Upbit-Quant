import os
import time
import requests
import pandas as pd
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("DataLoader")

class DataLoader:
    """
    Downloads and caches historical candlestick data from Bithumb and Upbit KRW markets.
    Ensures zero-cost local replay, offline backtesting, and full 1-year 2025 historical data access.
    """
    BASE_BITHUMB_URL = "https://api.bithumb.com"
    BASE_UPBIT_URL = "https://api.upbit.com/v1/candles"

    def __init__(self, cache_dir: str = "data"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_candlestick_data(self, symbol: str = "BTC_KRW", interval: str = "24h", year: Optional[int] = None, force_download: bool = False) -> pd.DataFrame:
        """
        Loads candlestick data for a symbol (e.g. BTC_KRW) and interval (e.g. 1h, 24h).
        If year=2025 is specified, fetches the complete 1-year historical series for 2025.
        """
        cache_filename = f"{symbol}_{interval}_year_{year}.csv" if year else f"{symbol}_{interval}.csv"
        cache_file = self.cache_dir / cache_filename

        if cache_file.exists() and not force_download:
            logger.info(f"Loading cached historical data from {cache_file}...")
            df = pd.read_csv(cache_file)
            df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
            return df

        if year == 2025:
            df = self._fetch_2025_year_dataset(symbol, interval)
            if not df.empty:
                df.to_csv(cache_file, index=False)
                logger.info(f"Cached 2025 full 1-year dataset ({len(df)} candles) to {cache_file}")
                return df

        # Fallback to Bithumb standard public endpoint
        logger.info(f"Downloading historical {interval} candles for {symbol} from Bithumb...")
        url = f"{self.BASE_BITHUMB_URL}/public/candlestick/{symbol}/{interval}"
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                data = res.json()
                if data.get("status") == "0000":
                    raw_candles = data.get("data", [])
                    if raw_candles:
                        df = pd.DataFrame(raw_candles, columns=["timestamp", "open", "close", "high", "low", "volume"])
                        df[["open", "close", "high", "low", "volume"]] = df[["open", "close", "high", "low", "volume"]].astype(float)
                        df["timestamp"] = df["timestamp"].astype(int)
                        df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")
                        df.to_csv(cache_file, index=False)
                        return df
        except Exception as e:
            logger.error(f"Failed to fetch data from Bithumb: {e}")

        if cache_file.exists():
            return pd.read_csv(cache_file)
        return pd.DataFrame()

    def _fetch_2025_year_dataset(self, symbol: str, interval: str) -> pd.DataFrame:
        """
        Fetches the complete 2025 (2025-01-01 to 2025-12-31) historical dataset from Korean Won exchange API.
        """
        market = f"KRW-{symbol.split('_')[0]}"
        logger.info(f"Fetching full 2025 1-year historical dataset for {market} ({interval})...")

        all_candles = []
        to_time = "2026-01-01T00:00:00Z"
        endpoint = "days" if interval in ("24h", "1d", "day") else "minutes/60"

        # Paginate backwards to cover all of 2025
        max_pages = 3 if endpoint == "days" else 45  # 365 daily candles or 8760 hourly candles
        for page in range(max_pages):
            url = f"{self.BASE_UPBIT_URL}/{endpoint}?market={market}&count=200&to={to_time}"
            try:
                res = requests.get(url, timeout=10).json()
                if not res or (isinstance(res, dict) and res.get("error")):
                    break
                all_candles.extend(res)
                to_time = res[-1]["candle_date_time_utc"] + "Z"
                time.sleep(0.05)
            except Exception as e:
                logger.warning(f"Pagination error at page {page}: {e}")
                break

        if not all_candles:
            return pd.DataFrame()

        df_raw = pd.DataFrame(all_candles)
        df_raw["datetime"] = pd.to_datetime(df_raw["candle_date_time_utc"])

        # Filter strictly for year 2025: 2025-01-01 to 2025-12-31
        df_2025 = df_raw[(df_raw["datetime"] >= "2025-01-01") & (df_raw["datetime"] <= "2025-12-31T23:59:59")].copy()
        df_2025 = df_2025.sort_values("datetime").reset_index(drop=True)

        # Standardize columns to [timestamp, open, close, high, low, volume, datetime]
        df_standard = pd.DataFrame({
            "timestamp": df_2025["datetime"].astype("int64") // 10**6,
            "open": df_2025["opening_price"].astype(float),
            "close": df_2025["trade_price"].astype(float),
            "high": df_2025["high_price"].astype(float),
            "low": df_2025["low_price"].astype(float),
            "volume": df_2025["candle_acc_trade_volume"].astype(float),
            "datetime": df_2025["datetime"]
        })

        logger.info(f"Loaded {len(df_standard)} candles for 2025 1-year trade ({df_standard['datetime'].min()} to {df_standard['datetime'].max()})")
        return df_standard
