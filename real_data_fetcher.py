import pandas as pd
import yfinance as yf

# خريطة لربط الفريمات الزمنية الخاصة بالبوت مع فريمات yfinance
TIMEFRAME_MAP = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1h": "1h",
    "4h": "1h", # yfinance يحدد أقصى حد لبعض الفريمات، لذا نضبطها بما يناسب المتاحة
    "1d": "1d"
}

def fetch_real_data(pair_name, tf_name, limit=100):
    """
    الدالة الرئيسية لجلب البيانات الحقيقية حسب نوع الزوج (فوركس، أسهم، أو كريبتو)
    """
    # تنظيف وتنسيق رمز الزوج ليتوافق مع تنسيق المنصات المالية (مثال: EURUSD=X أو BTC-USD)
    formatted_symbol = pair_name.replace("/", "")
    
    if "FOREX" in pair_name.upper() or len(formatted_symbol) == 6 and "=" not in formatted_symbol:
        # رموز الفوركس في yfinance تتبع اللاحقة =X (مثال: EURUSD=X)
        if not formatted_symbol.endswith("=X"):
            formatted_symbol = formatted_symbol + "=X"
    elif "CRYPTO" in pair_name.upper() or "BTC" in pair_name.upper() or "ETH" in pair_name.upper():
        if "-" not in formatted_symbol:
            formatted_symbol = formatted_symbol.replace("USDT", "-USD")

    interval = TIMEFRAME_MAP.get(tf_name, "5m")
    
    try:
        # جلب البيانات الحقيقية باستخدام yfinance
        df = yf.download(formatted_symbol, period="5d", interval=interval, progress=False)
        
        if df.empty:
            # محاولة بديلة في حال كان الرمز بصيغة أخرى
            df = yf.download(pair_name, period="5d", interval=interval, progress=False)
            
        if not df.empty:
            # إعادة تشكيل الأعمدة لتتوافق مع دوال التحليل الفني (تتطلب عمود 'close' للأسعار الإغلاقية)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            df = df.rename(columns={"Close": "close", "Open": "open", "High": "high", "Low": "low", "Volume": "volume"})
            
            if 'close' in df.columns:
                return df[['open', 'high', 'low', 'close', 'volume']].dropna().tail(limit)
                
    except Exception as e:
        print(f"Error fetching real data for {pair_name}: {e}")
        
    # إرجاع DataFrame فارغ في حال فشل الجلب
    return pd.DataFrame()
    
    
