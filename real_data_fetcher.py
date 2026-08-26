import os
import requests
import pandas as pd

TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h"]

BINANCE_INTERVAL_MAP = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
}

TWELVE_DATA_INTERVAL_MAP = {
    "1m": "1min",
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1h": "1h",
}


def _is_crypto_pair(pair_name: str) -> bool:
    crypto_symbols = ("BTC", "ETH", "USDT", "BNB", "SOL", "XRP", "DOGE", "ADA")
    cleaned = pair_name.upper().replace("/", "").replace(" ", "")
    return any(sym in cleaned for sym in crypto_symbols)


def fetch_binance_klines(pair_name: str, tf_name: str, limit: int = 150) -> pd.DataFrame:
    if tf_name not in BINANCE_INTERVAL_MAP:
        raise ValueError(f"الفريم '{tf_name}' غير مدعوم من Binance. الفريمات المتاحة: {list(BINANCE_INTERVAL_MAP)}")

    symbol = pair_name.upper().replace("/", "").replace(" ", "").replace("-", "")
    interval = BINANCE_INTERVAL_MAP[tf_name]

    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}

    resp = requests.get(url, params=params, timeout=10)
    if resp.status_code != 200:
        raise ValueError(
            f"تعذر جلب بيانات {symbol} من Binance (كود {resp.status_code}). "
            f"تأكد أن رمز الزوج صحيح (مثال صحيح: BTCUSDT)."
        )

    raw = resp.json()
    if not isinstance(raw, list) or len(raw) == 0:
        raise ValueError(f"لم يتم إرجاع أي شموع للزوج {symbol}.")

    df = pd.DataFrame(raw, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "num_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["time"] = pd.to_datetime(df["open_time"], unit="ms")
    return df[["time", "close"]]


def fetch_twelvedata_klines(pair_name: str, tf_name: str, limit: int = 150) -> pd.DataFrame:
    api_key = os.environ.get("TWELVE_DATA_API_KEY")
    if not api_key:
        raise ValueError(
            "لا يوجد مفتاح TWELVE_DATA_API_KEY. احصل على مفتاح مجاني من "
            "https://twelvedata.com/apikey وضعه في متغيرات البيئة."
        )

    if tf_name not in TWELVE_DATA_INTERVAL_MAP:
        raise ValueError(f"الفريم '{tf_name}' غير مدعوم. الفريمات المتاحة: {list(TWELVE_DATA_INTERVAL_MAP)}")

    interval = TWELVE_DATA_INTERVAL_MAP[tf_name]
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": pair_name.replace(" ", ""),
        "interval": interval,
        "outputsize": limit,
        "apikey": api_key,
    }

    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()

    if "values" not in data:
        msg = data.get("message", "استجابة غير متوقعة من Twelve Data")
        raise ValueError(f"تعذر جلب بيانات {pair_name}: {msg}")

    df = pd.DataFrame(data["values"])
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["time"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("time").reset_index(drop=True)
    return df[["time", "close"]]


def fetch_real_data(pair_name: str, tf_name: str, limit: int = 150) -> pd.DataFrame:
    if "OTC" in pair_name.upper():
        raise ValueError(
            f"الزوج '{pair_name}' هو زوج OTC تركيبي خاص بمنصة الخيارات الثنائية، "
            f"ولا يوجد له أي مصدر بيانات حقيقي متاح للعامة. "
            f"يمكن تحليل الأزواج الحقيقية (فوركس، أسهم، معادن أو كريبتو) فقط."
        )

    if _is_crypto_pair(pair_name):
        return fetch_binance_klines(pair_name, tf_name, limit)
    else:
        return fetch_twelvedata_klines(pair_name, tf_name, limit)
