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
        df = yf.download(tickers=ticker, period="5d", interval=interval, progress=False, multi_level_index=False)
        if df.empty or len(df) < 20:
            return None

        if 'Close' in df.columns:
            close = df['Close'].dropna()
            high = df['High'].dropna()
            low = df['Low'].dropna()
        else:
            close = df.iloc[:, 3].dropna()
            high = df.iloc[:, 1].dropna()
            low = df.iloc[:, 2].dropna()

        if len(close) < 20:
            return None

        # 1. RSI (14)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # 2. EMA 50
        span_val = 50 if len(close) >= 50 else len(close)
        ema50 = close.ewm(span=span_val, adjust=False).mean()

        # 3. Bollinger Bands (20, 2)
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        upper_band = sma20 + (std20 * 2)
        lower_band = sma20 - (std20 * 2)

        # 4. ATR لحساب SL / TP
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean()

        last_price = round(float(close.iloc[-1]), 4)
        last_rsi = round(float(rsi.fillna(50).iloc[-1]), 2)
        last_ema = round(float(ema50.iloc[-1]), 4)
        last_upper = round(float(upper_band.fillna(last_price).iloc[-1]), 4)
        last_lower = round(float(lower_band.fillna(last_price).iloc[-1]), 4)
        last_atr = float(atr.fillna(0).iloc[-1])

        if last_atr == 0:
            last_atr = last_price * 0.0015

        sl_buy = round(last_price - (last_atr * 1.5), 4)
        tp_buy = round(last_price + (last_atr * 2.5), 4)
        sl_sell = round(last_price + (last_atr * 1.5), 4)
        tp_sell = round(last_price - (last_atr * 2.5), 4)

        if last_price <= last_lower:
            bb_status = "📉 أسفل Bollinger Band (فرصة ارتداد صاعد)"
        elif last_price >= last_upper:
            bb_status = "📈 أعلى Bollinger Band (فرصة ارتداد هابط)"
        else:
            bb_status = "↔️ داخل Bollinger Bands"

        is_strong_buy = (last_rsi <= 30) and (last_price <= last_lower) and (last_price > last_ema)
        is_strong_sell = (last_rsi >= 70) and (last_price >= last_upper) and (last_price < last_ema)

        trend = "📈 صاعد (Above EMA)" if last_price > last_ema else "📉 هابط (Below EMA)"

        return {
            "price": last_price,
            "rsi": last_rsi,
            "trend": trend,
            "bb_status": bb_status,
            "is_strong_buy": is_strong_buy,
            "is_strong_sell": is_strong_sell,
            "sl_buy": sl_buy,
            "tp_buy": tp_buy,
            "sl_sell": sl_sell,
            "tp_sell": tp_sell
        }
    except Exception as e:
        print(f"Error: {e}")
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
                            alert_msg = (
                                f"🚨 **تنبيه فرصة شراء قوية جداً!** 🟢🟢\n\n"
                                f"الزوج: **{name}**\n"
                                f"السعر: `{data['price']}`\n"
                                f"RSI: `{data['rsi']}`\n"
                                f"🛑 **SL:** `{data['sl_buy']}`\n"
                                f"🎯 **TP:** `{data['tp_buy']}`"
                            )
                        elif data["is_strong_sell"]:
                            alert_msg = (
                                f"🚨 **تنبيه فرصة بيع قوية جداً!** 🔴🔴\n\n"
                                f"الزوج: **{name}**\n"
                                f"السعر: `{data['price']}`\n"
                                f"RSI: `{data['rsi']}`\n"
                                f"🛑 **SL:** `{data['sl_sell']}`\n"
                                f"🎯 **TP:** `{data['tp_sell']}`"
                            )

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
                    sltp_info = f"🛑 **وقف الخسارة (SL):** `{res['sl_buy']}`\n🎯 **جني الأرباح (TP):** `{res['tp_buy']}`"
                elif res["rsi"] <= 30:
                    signal = "🟢 **إشارة شراء (BUY)**"
                    sltp_info = f"🛑 **وقف الخسارة (SL):** `{res['sl_buy']}`\n🎯 **جني الأرباح (TP):** `{res['tp_buy']}`"
                elif res["is_strong_sell"]:
                    signal = "🔴 **إشارة بيع قوية جداً (Strong SELL)**"
                    sltp_info = f"🛑 **وقف الخسارة (SL):** `{res['sl_sell']}`\n🎯 **جني الأرباح (TP):** `{res['tp_sell']}`"
                elif res["rsi"] >= 70:
                    signal = "🔴 **إشارة بيع (SELL)**"
                    sltp_info = f"🛑 **وقف الخسارة (SL):** `{res['sl_sell']}`\n🎯 **جني الأرباح (TP):** `{res['tp_sell']}`"
                else:
                    signal = "⚪ **حالة محايدة (Wait / No Trade)**"
                    sltp_info = f"💡 *مستويات الشراء:* SL `{res['sl_buy']}` | TP `{res['tp_buy']}`\n💡 *مستويات البيع:* SL `{res['sl_sell']}` | TP `{res['tp_sell']}`"

                output = (
                    f"📊 **تحليل متقدم لـ {asset}**\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"⏱️ **الإطار الزمني:** {trade_duration}\n"
                    f"💵 **السعر الحالي:** `{res['price']}`\n"
                    f"📈 **قيمة RSI:** `{res['rsi']}`\n"
                    f"📉 **الاتجاه العام (EMA 50):** {res['trend']}\n"
                    f"🎯 **حالة بولينجر:** {res['bb_status']}\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"🎯 **التوصية:**\n{signal}\n\n"
                    f"📐 **المستويات المقترحة (MT5):**\n{sltp_info}"
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

    print("Bot with BB, RSI, EMA & SL/TP is running...")
    bot.infinity_polling(timeout=60, long_polling_timeout=1)
    
    
    
    
    
    
    
