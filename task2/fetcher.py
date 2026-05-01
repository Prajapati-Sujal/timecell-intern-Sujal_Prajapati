"""
Task 02 — Market Data Fetcher
Individual asset fetchers with graceful error handling.
Assets: BTC (crypto), NIFTY50 (index), GOLD (commodity)
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional

import requests
import yfinance as yf

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

IST = timezone(timedelta(hours=5, minutes=30))


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class AssetPrice:
    name: str
    symbol: str
    price: float
    currency: str
    fetched_at: datetime
    source: str

    def price_display(self) -> str:
        return f"{self.price:,.2f}"

    def time_display(self) -> str:
        return self.fetched_at.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S IST")


# ---------------------------------------------------------------------------
# Individual fetchers
# ---------------------------------------------------------------------------

def fetch_btc() -> Optional[AssetPrice]:
    """
    Fetch BTC/USD from CoinGecko public API (no key required).
    Docs: https://www.coingecko.com/en/api
    """
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin",
        "vs_currencies": "usd",
    }
    try:
        log.info("Fetching BTC price from CoinGecko...")
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        price = data["bitcoin"]["usd"]
        return AssetPrice(
            name="Bitcoin",
            symbol="BTC",
            price=price,
            currency="USD",
            fetched_at=datetime.now(timezone.utc),
            source="CoinGecko",
        )
    except requests.exceptions.ConnectionError:
        log.error("BTC fetch failed — no internet connection or CoinGecko is unreachable.")
    except requests.exceptions.Timeout:
        log.error("BTC fetch failed — request timed out after 10s.")
    except requests.exceptions.HTTPError as e:
        log.error(f"BTC fetch failed — HTTP {e.response.status_code}: {e.response.reason}")
    except (KeyError, ValueError) as e:
        log.error(f"BTC fetch failed — unexpected response format: {e}")
    return None


def fetch_nifty50() -> Optional[AssetPrice]:
    """
    Fetch NIFTY 50 index price using yfinance (Yahoo Finance, no key required).
    Ticker: ^NSEI
    """
    try:
        log.info("Fetching NIFTY50 price from Yahoo Finance...")
        ticker = yf.Ticker("^NSEI")
        info = ticker.fast_info
        price = info.last_price

        if price is None or price != price:   # NaN guard
            raise ValueError("Received null/NaN price from yfinance.")

        return AssetPrice(
            name="NIFTY 50",
            symbol="NIFTY50",
            price=round(price, 2),
            currency="INR",
            fetched_at=datetime.now(timezone.utc),
            source="Yahoo Finance",
        )
    except Exception as e:
        log.error(f"NIFTY50 fetch failed — {type(e).__name__}: {e}")
    return None


def fetch_gold() -> Optional[AssetPrice]:
    """
    Fetch Gold price (INR per 10g) using yfinance.
    GC=F is Gold Futures in USD/oz. We convert to INR/10g using USD→INR rate.
    """
    try:
        log.info("Fetching GOLD price from Yahoo Finance...")

        # Gold futures (USD per troy oz)
        gold_ticker   = yf.Ticker("GC=F")
        gold_usd_oz   = gold_ticker.fast_info.last_price

        # USD/INR exchange rate
        fx_ticker     = yf.Ticker("INR=X")
        usd_to_inr    = fx_ticker.fast_info.last_price

        if gold_usd_oz is None or usd_to_inr is None:
            raise ValueError("Received null price for gold or FX rate.")

        # Conversions:
        # 1 troy oz = 31.1035 grams → price per gram in USD → × 10 → per 10g → × INR rate
        GRAMS_PER_OZ  = 31.1035
        gold_inr_10g  = (gold_usd_oz / GRAMS_PER_OZ) * 10 * usd_to_inr

        return AssetPrice(
            name="Gold",
            symbol="GOLD",
            price=round(gold_inr_10g, 2),
            currency="INR/10g",
            fetched_at=datetime.now(timezone.utc),
            source="Yahoo Finance (GC=F × INR=X)",
        )
    except Exception as e:
        log.error(f"GOLD fetch failed — {type(e).__name__}: {e}")
    return None


# ---------------------------------------------------------------------------
# Fetch all — always returns list (with None entries replaced by error rows)
# ---------------------------------------------------------------------------

def fetch_all_assets() -> list[Optional[AssetPrice]]:
    """
    Fetch all 3 assets. Never raises — individual failures are logged and
    returned as None so the table can still render the successful ones.
    """
    fetchers = [fetch_btc, fetch_nifty50, fetch_gold]
    results  = []
    for fn in fetchers:
        results.append(fn())
    return results