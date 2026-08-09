import os
import time
import threading
import telebot
from telebot import types
import yfinance as yf
import pandas as pd

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

USERS_FILE = "users.txt"

# قائمة شاملة لجميع الأزواج والأسواق
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

def load_users():
    if not os.path.exists(USERS_FILE):
        return set()
    with open(USERS_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_user(chat_id):
    users = load_users()
    if str(chat_id) not in users:
        with open(USERS_FILE, "a") as f:
            f.write(f"{chat_id}\n")

def analyze_asset(ticker, interval="5m"):
    try:
        df = yf.download(tickers=ticker, period="5d", interval=interval, progress=False)
        if df.empty or len(df) < 50:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            close = df['Close'][ticker].dropna()
        else:
            close = df['Close'].dropna()

        # حساب RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # حساب EMA 50
        ema50 = close.ewm(span=50, adjust=False).mean()

        last_price = round(float(close.iloc[-1]), 4)
        last_rsi = round(float(rsi.fillna(50).iloc[-1]), 2)
        last_ema = round(float(ema50.iloc[-1]), 4)

        is_strong_buy = (last_rsi <= 30) and (last_price > last_ema)
        is_strong_sell = (last_rsi >= 70) and (last_price < last_ema)

        trend = "📈 صاعد (Above EMA)" if last_price > last_ema else "📉 هابط (Below EMA)"

        return {
            "price": last_price,
            "rsi": last_rsi,
            "trend": trend,
            "is_strong_buy": is_strong_buy,
            "is_strong_sell": is_strong_sell
        }
    except Exception:
        return None

# دالة الفحص الدوري للتنبيهات (يفحص جميع العملات كل 5 دقائق)
def auto_scanner():
    while True:
        try:
            users = load_users()
            if users:
                for name, ticker in SYMBOL_MAP.items():
                    # تجنب تكرار الرموز المرادفة
                    if "/" not in name and name not in ["Bitcoin", "Ethereum", "الذهب (Gold)", "الفضة (Silver)", "النفط (Crude Oil)"]:
                        continue
                        
                    data = analyze_asset(ticker, interval="5m")
                    if data:
                        alert_msg = None
                        if data["is_strong_buy"]:
                            alert_msg = f"🚨 **تنبيه فرصة شراء قوية!** 🟢\n\nالزوج: **{name}**\nالسعر: `{data['price']}`\nRSI: `{data['rsi']}`\nالاتجاه: صاعد (فوق EMA 50)"
                        elif data["is_strong_sell"]:
                            alert_msg = f"🚨 **تنبيه فرصة بيع قوية!** 🔴\n\nالزوج: **{name}**\nالسعر: `{data['price']}`\nRSI: `{data['rsi']}`\nالاتجاه: هابط (تحت EMA 50)"

                        if alert_msg:
                            for user_id in users:
                                try:
                                    bot.send_message(user_id, alert_msg, parse_mode="Markdown")
                                except Exception:
                                    pass
            time.sleep(300) # فحص كل 5 دقائق
        except Exception as e:
            print(f"Error in scanner: {e}")
            time.sleep(60)

# القائمة التفاعلية في التلجرام
@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    save_user(message.chat.id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("EUR/USD 🇪🇺🇺🇸", callback_data="EURUSD"),
        types.InlineKeyboardButton("GBP/USD 🇬🇧🇺🇸", callback_data="GBPUSD"),
        types.InlineKeyboardButton("USD/JPY 🇺🇸🇯🇵", callback_data="USDJPY"),
        types.InlineKeyboardButton("USD/CAD 🇺🇸🇨🇦", callback_data="USDCAD"),
        types.InlineKeyboardButton("AUD/USD 🇦🇺🇺🇸", callback_data="AUDUSD"),
        types.InlineKeyboardButton("USD/CHF 🇺🇸🇨🇭", callback_data="USDCHF"),
        types.InlineKeyboardButton("NZD/USD 🇳🇿🇺🇸", callback_data="NZDUSD"),
        types.InlineKeyboardButton("EUR/GBP 🇪🇺🇬🇧", callback_data="EURGBP"),
        types.InlineKeyboardButton("الذهب (Gold) 🥇", callback_data="XAUUSD"),
        types.InlineKeyboardButton("الفضة (Silver) 🥈", callback_data="XAGUSD"),
        types.InlineKeyboardButton("النفط (Crude Oil) 🛢️", callback_data="CL"),
        types.InlineKeyboardButton("Bitcoin ₿", callback_data="BTC"),
        types.InlineKeyboardButton("Ethereum 💎", callback_data="ETH")
    ]
    markup.add(*buttons)
    bot.send_message(
        message.chat.id, 
        "📊 **مرحباً بك! تم تفعيل التنبيهات التلقائية لك.**\nاختر الزوج للحصول على تحليل مباشر:", 
        reply_markup=markup
    )

def get_timeframe_keyboard(asset_key):
    markup = types.InlineKeyboardMarkup(row_width=3)
    btn1 = types.InlineKeyboardButton("⏱️ 1 دقيقة", callback_data=f"{asset_key}|1m")
    btn2 = types.InlineKeyboardButton("⏱️ 5 دقائق", callback_data=f"{asset_key}|5m")
    btn3 = types.InlineKeyboardButton("⏱️ 15 دقيقة", callback_data=f"{asset_key}|15m")
    markup.add(btn1, btn2, btn3)
    return markup

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        bot.answer_callback_query(call.id)
        data = call.data
        
        if "|" in data:
            asset, interval = data.split("|")
            ticker = SYMBOL_MAP.get(asset, asset)
            bot.send_message(call.message.chat.id, f"⏳ جاري تحليل {asset}...")
            
            res = analyze_asset(ticker, interval)
            if res:
                trade_duration = "دقيقة واحدة (1m)" if interval == "1m" else ("5 دقائق (5m)" if interval == "5m" else "15 دقيقة (15m)")
                
                if res["is_strong_buy"]:
                    signal = "🟢 **إشارة شراء قوية جداً (Strong BUY)**"
                elif res["rsi"] <= 30:
                    signal = "🟢 **إشارة شراء (BUY)**"
                elif res["is_strong_sell"]:
                    signal = "🔴 **إشارة بيع قوية جداً (Strong SELL)**"
                elif res["rsi"] >= 70:
                    signal = "🔴 **إشارة بيع (SELL)**"
                else:
                    signal = "⚪ **حالة محايدة (Wait / No Trade)**"

                output = (
                    f"📊 **تحليل متقدم لـ {asset}**\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"⏱️ **الإطار الزمني:** {trade_duration}\n"
                    f"💵 **السعر الحالي:** `{res['price']}`\n"
                    f"📈 **قيمة RSI:** `{res['rsi']}`\n"
                    f"📉 **الاتجاه العام (EMA 50):** {res['trend']}\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🎯 **التوصية:**\n{signal}"
                )
                bot.send_message(call.message.chat.id, output, parse_mode="Markdown")
            else:
                bot.send_message(call.message.chat.id, f"⚠️ تعذر جلب بيانات {asset} حالياً.")
        else:
            bot.send_message(
                call.message.chat.id, 
                f"⏱️ **اختر الإطار الزمني للتحليل الخاص بـ ({data}):**", 
                reply_markup=get_timeframe_keyboard(data),
                parse_mode="Markdown"
            )

if __name__ == "__main__":
    scanner_thread = threading.Thread(target=auto_scanner)
    scanner_thread.daemon = True
    scanner_thread.start()

    print("Bot with Full Pairs & Auto-Alerts is running...")
    bot.infinity_polling(timeout=60, long_polling_timeout=1)
    
    
    
    
    
