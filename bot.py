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

SYMBOL_MAP = {
    "EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "JPY=X",
    "USD/CAD": "CAD=X", "AUD/USD": "AUDUSD=X", "USD/CHF": "CHF=X",
    "NZD/USD": "NZDUSD=X", "EUR/GBP": "EURGBP=X", "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X", "EUR/CAD": "EURCAD=X", "EUR/AUD": "EURAUD=X",
    "EUR/CHF": "EURCHF=X", "GBP/CAD": "GBPCAD=X", "GBP/AUD": "GBPAUD=X",
    "GBP/CHF": "GBPCHF=X", "AUD/CAD": "AUDCAD=X", "AUD/JPY": "AUDJPY=X",
    "AUD/NZD": "AUDNZD=X", "NZD/JPY": "NZDJPY=X", "CAD/JPY": "CADJPY=X",
    "CHF/JPY": "CHFJPY=X",
    "الذهب (Gold)": "GC=F", "الفضة (Silver)": "SI=F", "النفط (Crude Oil)": "CL=F",
    "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD",
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

def remove_user(chat_id):
    users = load_users()
    if str(chat_id) in users:
        users.remove(str(chat_id))
        with open(USERS_FILE, "w") as f:
            for uid in users:
                f.write(f"{uid}\n")

def analyze_asset(ticker, interval="5m"):
    try:
        df = yf.download(tickers=ticker, period="5d", interval=interval, progress=False)
        if df.empty or len(df) < 50:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            close = df['Close'][ticker].dropna()
        else:
            close = df['Close'].dropna()

        # 1. RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # 2. EMA 50
        ema50 = close.ewm(span=50, adjust=False).mean()

        # 3. Bollinger Bands (20, 2)
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        upper_band = sma20 + (std20 * 2)
        lower_band = sma20 - (std20 * 2)

        last_price = round(float(close.iloc[-1]), 4)
        last_rsi = round(float(rsi.fillna(50).iloc[-1]), 2)
        last_ema = round(float(ema50.iloc[-1]), 4)
        last_upper = round(float(upper_band.iloc[-1]), 4)
        last_lower = round(float(lower_band.iloc[-1]), 4)

        # تحديد موضع السعر بالنسبة لـ Bollinger Bands
        if last_price <= last_lower:
            bb_status = "📉 أسفل Bollinger Band (فرصة ارتداد صاعد)"
        elif last_price >= last_upper:
            bb_status = "📈 أعلى Bollinger Band (فرصة ارتداد هابط)"
        else:
            bb_status = "↔️ داخل Bollinger Bands"

        # الشروط المعززة بإضافة Bollinger Bands
        is_strong_buy = (last_rsi <= 30) and (last_price <= last_lower) and (last_price > last_ema)
        is_strong_sell = (last_rsi >= 70) and (last_price >= last_upper) and (last_price < last_ema)

        trend = "📈 صاعد (Above EMA)" if last_price > last_ema else "📉 هابط (Below EMA)"

        return {
            "price": last_price,
            "rsi": last_rsi,
            "trend": trend,
            "bb_status": bb_status,
            "upper_bb": last_upper,
            "lower_bb": last_lower,
            "is_strong_buy": is_strong_buy,
            "is_strong_sell": is_strong_sell
        }
    except Exception:
        return None

def auto_scanner():
    while True:
        try:
            users = load_users()
            if users:
                for name, ticker in SYMBOL_MAP.items():
                    if "/" not in name and name not in ["Bitcoin", "Ethereum", "الذهب (Gold)", "الفضة (Silver)", "النفط (Crude Oil)"]:
                        continue
                        
                    data = analyze_asset(ticker, interval="5m")
                    if data:
                        alert_msg = None
                        if data["is_strong_buy"]:
                            alert_msg = f"🚨 **تنبيه فرصة شراء قوية جداً!** 🟢🟢\n\nالزوج: **{name}**\nالسعر: `{data['price']}`\nRSI: `{data['rsi']}`\nBollinger: كسرت الحد السفلي\nالاتجاه: فوق EMA 50"
                        elif data["is_strong_sell"]:
                            alert_msg = f"🚨 **تنبيه فرصة بيع قوية جداً!** 🔴🔴\n\nالزوج: **{name}**\nالسعر: `{data['price']}`\nRSI: `{data['rsi']}`\nBollinger: كسرت الحد العلوي\nالاتجاه: تحت EMA 50"

                        if alert_msg:
                            for user_id in users:
                                try:
                                    bot.send_message(user_id, alert_msg, parse_mode="Markdown")
                                except Exception:
                                    pass
            time.sleep(300)
        except Exception as e:
            print(f"Error in scanner: {e}")
            time.sleep(60)

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    save_user(message.chat.id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn_enable = types.InlineKeyboardButton("🔔 تفعيل التنبيهات", callback_data="ENABLE_ALERTS")
    btn_disable = types.InlineKeyboardButton("🔕 إيقاف التنبيهات", callback_data="DISABLE_ALERTS")
    markup.add(btn_enable, btn_disable)

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
        "📊 **مرحباً بك! اختر الخدمة المطلوبة أو ابدأ بالتحليل المباشر:**", 
        reply_markup=markup,
        parse_mode="Markdown"
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
        
        if data == "ENABLE_ALERTS":
            save_user(call.message.chat.id)
            bot.send_message(call.message.chat.id, "🔔 **تم تفعيل التنبيهات التلقائية بنجاح!**")
            return
        elif data == "DISABLE_ALERTS":
            remove_user(call.message.chat.id)
            bot.send_message(call.message.chat.id, "🔕 **تم إيقاف التنبيهات التلقائية.**")
            return

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
                    f"🎯 **حالة بولينجر:** {res['bb_status']}\n"
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

    print("Bot with BB is running...")
    bot.infinity_polling(timeout=60, long_polling_timeout=1)
    
    
    
    
    
    
