import os
import telebot
import yfinance as yf
import pandas as pd
import ta

# جلب التوكن من متغيرات البيئة في Render
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

def analyze_forex_pair(symbol="EURUSD=X", timeframe="5m", period="1d"):
    try:
        data = yf.download(tickers=symbol, period=period, interval=timeframe)
        if data.empty:
            return "عذراً، تعذر جلب بيانات السوق حالياً."

        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df['EMA_Fast'] = ta.trend.ema_indicator(df['Close'], window=9)
        df['EMA_Slow'] = ta.trend.ema_indicator(df['Close'], window=21)
        df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
        
        macd = ta.trend.MACD(df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        
        latest = df.iloc[-1]
        price = round(float(latest['Close']), 5)
        rsi_val = round(float(latest['RSI']), 2)
        
        buy_signal = (
            (latest['EMA_Fast'] > latest['EMA_Slow']) and 
            (50 < latest['RSI'] < 70) and 
            (latest['MACD'] > latest['MACD_Signal'])
        )
        
        sell_signal = (
            (latest['EMA_Fast'] < latest['EMA_Slow']) and 
            (30 < latest['RSI'] < 50) and 
            (latest['MACD'] < latest['MACD_Signal'])
        )
        
        if buy_signal:
            return f"🟢 إشارة شراء قوية (CALL / BUY)\nالزوج: {symbol}\nالسعر: {price}\nRSI: {rsi_val}"
        elif sell_signal:
            return f"🔴 إشارة بيع قوية (PUT / SELL)\nالزوج: {symbol}\nالسعر: {price}\nRSI: {rsi_val}"
        else:
            return f"⚪ السوق في حالة تذبذب (انتظر)\nالزوج: {symbol}\nالسعر: {price}\nRSI: {rsi_val}"
    except Exception as e:
        return f"حدث خطأ أثناء التحليل: {e}"

# استقبال أمر /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً بك! أرسل /eurusd للحصول على إشارة EUR/USD أو /gold للحصول على إشارة الذهب.")

# استقبال أمر /eurusd
@bot.message_handler(commands=['eurusd'])
def get_eurusd(message):
    bot.reply_to(message, "جاري تحليل سوق EUR/USD...")
    result = analyze_forex_pair("EURUSD=X")
    bot.reply_to(message, result)

# استقبال أمر /gold
@bot.message_handler(commands=['gold'])
def get_gold(message):
    bot.reply_to(message, "جاري تحليل سوق الذهب...")
    result = analyze_forex_pair("GC=F")
    bot.reply_to(message, result)

# تشغيل البوت بشكل مستمر
bot.infinity_polling()


    
    
    
    
    
    
    
    
    
    
    
