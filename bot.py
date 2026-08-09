import os
import telebot
from telebot import types
import yfinance as yf
import pandas as pd

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

SYMBOL_MAP = {
    # الفوركس
    "EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "JPY=X",
    "USD/CAD": "CAD=X", "AUD/USD": "AUDUSD=X", "USD/CHF": "CHF=X",
    "NZD/USD": "NZDUSD=X", "EUR/GBP": "EURGBP=X", "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X", "EUR/CAD": "EURCAD=X", "EUR/AUD": "EURAUD=X",
    "EUR/CHF": "EURCHF=X", "GBP/CAD": "GBPCAD=X", "GBP/AUD": "GBPAUD=X",
    "GBP/CHF": "GBPCHF=X", "AUD/CAD": "AUDCAD=X", "AUD/JPY": "AUDJPY=X",
    "AUD/NZD": "AUDNZD=X", "NZD/JPY": "NZDJPY=X", "CAD/JPY": "CADJPY=X",
    "CHF/JPY": "CHFJPY=X",
    # السلع والمعادن والعملات الرقمية
    "الذهب (Gold)": "GC=F", "الفضة (Silver)": "SI=F", "النفط (Crude Oil)": "CL=F",
    "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD",
    # الرموز المباشرة
    "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "USDJPY": "JPY=X",
    "USDCAD": "CAD=X", "USDCHF": "CHF=X", "AUDUSD": "AUDUSD=X",
    "NZDUSD": "NZDUSD=X", "EURGBP": "EURGBP=X", "EURJPY": "EURJPY=X",
    "GBPJPY": "GBPJPY=X", "XAUUSD": "GC=F", "XAGUSD": "SI=F",
    "BTC": "BTC-USD", "ETH": "ETH-USD"
}

def analyze_asset(ticker, interval="1m"):
    try:
        trade_duration = "دقيقة واحدة (1m)" if interval == "1m" else ("5 دقائق (5m)" if interval == "5m" else "15 دقيقة (15m)")
        period = "5d" if interval in ["1m", "5m"] else "1mo"
        
        df = yf.download(tickers=ticker, period=period, interval=interval, progress=False)
        
        if df.empty or len(df) < 50:
            return f"⚠️ البيانات غير متاحة حالياً للرمز {ticker}."

        if isinstance(df.columns, pd.MultiIndex):
            close = df['Close'][ticker].dropna()
        else:
            close = df['Close'].dropna()

        # 1. حساب مؤشر RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # 2. حساب المتوسط المتحرك الاسي EMA 50
        ema50 = close.ewm(span=50, adjust=False).mean()

        last_price = round(float(close.iloc[-1]), 4)
        last_rsi = round(float(rsi.fillna(50).iloc[-1]), 2)
        last_ema = round(float(ema50.iloc[-1]), 4)

        # تحديد الاتجاه العام (Trend)
        trend = "📈 صاعد (Above EMA)" if last_price > last_ema else "📉 هابط (Below EMA)"

        # بناء التوصية المعززة
        if last_rsi <= 30 and last_price > last_ema:
            signal = "🟢 **إشارة شراء قوية جداً (Strong BUY)**\n*(تشبع بيعي مع اتجاه صاعد)*"
        elif last_rsi <= 30:
            signal = "🟢 **إشارة شراء متوسطة (BUY)**\n*(تشبع بيعي)*"
        elif last_rsi >= 70 and last_price < last_ema:
            signal = "🔴 **إشارة بيع قوية جداً (Strong SELL)**\n*(تشبع شرائي مع اتجاه هابط)*"
        elif last_rsi >= 70:
            signal = "🔴 **إشارة بيع متوسطة (SELL)**\n*(تشبع شرائي)*"
        else:
            signal = "⚪ **حالة محايدة (Wait / No Trade)**"

        return (
            f"📊 **تحليل متقدم لـ {ticker}**\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⏱️ **الإطار الزمني:** {trade_duration}\n"
            f"💵 **السعر الحالي:** `{last_price}`\n"
            f"📈 **قيمة RSI:** `{last_rsi}`\n"
            f"📉 **الاتجاه العام (EMA 50):** {trend}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎯 **التوصية:**\n{signal}"
        )
    except Exception as e:
        return f"⚠️ حدث خطأ أثناء التحليل: {str(e)}"

def get_timeframe_keyboard(asset_key):
    markup = types.InlineKeyboardMarkup(row_width=3)
    btn1 = types.InlineKeyboardButton("⏱️ 1 دقيقة", callback_data=f"{asset_key}|1m")
    btn2 = types.InlineKeyboardButton("⏱️ 5 دقائق", callback_data=f"{asset_key}|5m")
    btn3 = types.InlineKeyboardButton("⏱️ 15 دقيقة", callback_data=f"{asset_key}|15m")
    markup.add(btn1, btn2, btn3)
    return markup

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("EUR/USD 🇪🇺🇺🇸", callback_data="EURUSD"),
        types.InlineKeyboardButton("GBP/USD 🇬🇧🇺🇸", callback_data="GBPUSD"),
        types.InlineKeyboardButton("USD/JPY 🇺🇸🇯🇵", callback_data="USDJPY"),
        types.InlineKeyboardButton("USD/CAD 🇺🇸🇨🇦", callback_data="USDCAD"),
        types.InlineKeyboardButton("الذهب (Gold) 🥇", callback_data="XAUUSD"),
        types.InlineKeyboardButton("الفضة (Silver) 🥈", callback_data="XAGUSD"),
        types.InlineKeyboardButton("النفط (Crude Oil) 🛢️", callback_data="CL"),
        types.InlineKeyboardButton("Bitcoin ₿", callback_data="BTC"),
        types.InlineKeyboardButton("Ethereum 💎", callback_data="ETH")
    ]
    markup.add(*buttons)
    bot.send_message(message.chat.id, "📊 **اختر الزوج أو الأصل لاستخراج الإشارة:**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        bot.answer_callback_query(call.id)
        data = call.data
        
        if "|" in data:
            asset, interval = data.split("|")
            ticker = SYMBOL_MAP.get(asset, asset)
            bot.send_message(call.message.chat.id, f"⏳ جاري تحليل {asset} بواسطة RSI + EMA...")
            result = analyze_asset(ticker, interval)
            bot.send_message(call.message.chat.id, result, parse_mode="Markdown")
        else:
            bot.send_message(
                call.message.chat.id, 
                f"⏱️ **اختر الإطار الزمني للتحليل الخاص بـ ({data}):**", 
                reply_markup=get_timeframe_keyboard(data),
                parse_mode="Markdown"
            )

if __name__ == "__main__":
    print("Bot is running with EMA & RSI indicators...")
    bot.infinity_polling(timeout=60, long_polling_timeout=1)
    
    
    
    
