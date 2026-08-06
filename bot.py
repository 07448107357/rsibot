import yfinance as yf
import pandas as pd
import ta

def analyze_forex_pair(symbol="EURUSD=X", timeframe="5m", period="1d"):
    """
    جلب بيانات الزوج وتحليله
    symbol: رمز الزوج في Yahoo Finance (مثل EURUSD=X أو GBPUSD=X أو GC=F للذهب)
    timeframe: الفريم الزمني (1m, 5m, 15m, 1h)
    """
    # 1. جلب بيانات الأسعار من السوق الحقيقي
    data = yf.download(tickers=symbol, period=period, interval=timeframe)
    
    if data.empty:
        return "فشل في جلب البيانات، تأكد من الرمز."

    # تنظيف البيانات
    df = data.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 2. حساب المؤشرات الفنية (EMA, RSI, MACD)
    df['EMA_Fast'] = ta.trend.ema_indicator(df['Close'], window=9)
    df['EMA_Slow'] = ta.trend.ema_indicator(df['Close'], window=21)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    
    # 3. فحص أحدث شمعة في السوق
    latest = df.iloc[-1]
    price = round(latest['Close'], 5)
    rsi_val = round(latest['RSI'], 2)
    
    # شروط الإشارات
    buy_signal = (
        (latest['EMA_Fast'] > latest['EMA_Slow']) and 
        (latest['RSI'] > 50 and latest['RSI'] < 70) and 
        (latest['MACD'] > latest['MACD_Signal'])
    )
    
    sell_signal = (
        (latest['EMA_Fast'] < latest['EMA_Slow']) and 
        (latest['RSI'] < 50 and latest['RSI'] > 30) and 
        (latest['MACD'] < latest['MACD_Signal'])
    )
    
    if buy_signal:
        return f"🟢 إشارة شراء قوية (CALL / BUY)\nالزوج: {symbol}\nالسعر: {price}\nRSI: {rsi_val}"
    elif sell_signal:
        return f"🔴 إشارة بيع قوية (PUT / SELL)\nالزوج: {symbol}\nالسعر: {price}\nRSI: {rsi_val}"
    else:
        return f"⚪ السوق في حالة تذبذب (انتظر)\nالزوج: {symbol}\nالسعر: {price}\nRSI: {rsi_val}"

# تجربة الكود على زوج اليورو/دولار
print(analyze_forex_pair("EURUSD=X", timeframe="5m"))

    
    
    
    
    
    
    
    
    
    
    
