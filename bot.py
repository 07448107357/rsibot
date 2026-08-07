import os
import time
import telebot
from telebot import types
import yfinance as yf
import pandas as pd

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

PAIRS = {
    # --- أزواج العملات الرئيسية (Majors) ---
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "AUD/USD": "AUDUSD=X",
    "NZD/USD": "NZDUSD=X",
    "USD/JPY": "USDJPY=X",
    "USD/CHF": "USDCHF=X",
    "USD/CAD": "USDCAD=X",

    # --- أزواج اليورو (EUR Pairs) ---
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "EUR/CHF": "EURCHF=X",
    "EUR/CAD": "EURCAD=X",
    "EUR/AUD": "EURAUD=X",
    "EUR/NZD": "EURNZD=X",

    # --- أزواج الباوند (GBP Pairs) ---
    "GBP/JPY": "GBPJPY=X",
    "GBP/CHF": "GBPCHF=X",
    "GBP/CAD": "GBPCAD=X",
    "GBP/AUD": "GBPAUD=X",
    "GBP/NZD": "GBPNZD=X",

    # --- أزواج الين والفرنك والكرونا (Cross Pairs) ---
    "AUD/JPY": "AUDJPY=X",
    "AUD/CAD": "AUDCAD=X",
    "AUD/NZD": "AUDNZD=X",
    "AUD/CHF": "AUDCHF=X",
    "CAD/JPY": "CADJPY=X",
    "CAD/CHF": "CADCHF=X",
    "CHF/JPY": "CHFJPY=X",
    "NZD/JPY": "NZDJPY=X",
    "NZD/CAD": "NZDCAD=X",
    "NZD/CHF": "NZDCHF=X",

    # --- المعادن والسلع (Commodities) ---
    "Gold (XAU/USD)": "GC=F",
    "Silver (XAG/USD)": "SI=F",
    "Crude Oil (USOIL)": "CL=F",

    # --- الأسهم العالمية المتاحة في المنصة (Stocks) ---
    "Apple 🍎": "AAPL",
    "Amazon 📦": "AMZN",
    "McDonald's 🍔": "MCD",
    "Meta (Facebook) 🌐": "META",
    "Google 🔍": "GOOGL",
    "Tesla ⚡️": "TSLA",
    "Microsoft 💻": "MSFT",
    "Boeing ✈️": "BA",
    "Intel 💻": "INTC"
}

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_analysis(symbol_key):
    ticker = PAIRS.get(symbol_key, symbol_key)
    try:
        df = yf.download(tickers=ticker, period="1d", interval="5m", progress=False)
        if df.empty or len(df) < 30:
            return "❌ لا تتوفر البيانات الكافية لهذا الزوج حالياً"

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df['RSI'] = calculate_rsi(df['Close'])
        df['SMA20'] = df['Close'].rolling(window=20).mean()
        
        latest = df.iloc[-1]
        price = round(float(latest['Close']), 4)
        rsi = round(float(latest['RSI']), 2)
        sma = float(latest['SMA20'])

        support = round(float(df['Low'].tail(20).min()), 4)
        resistance = round(float(df['High'].tail(20).max()), 4)

        # 1. تحديد الاتجاه بناءً على المتوسط المتحرك (SMA20)
        if price > sma:
            direction = "صاعد ⬆️"
        else:
            direction = "هابط ⬇️"

        # 2. تحديد التوصية بشرط التوافق مع الاتجاه العام
        if price > sma and rsi < 45:
            signal = "🟢 BUY SIGNAL (CALL / UP)"
        elif price < sma and rsi > 55:
            signal = "🔴 SELL SIGNAL (PUT / DOWN)"
        else:
            signal = "⚪️ NEUTRAL (WAIT)"

        msg = (
            f"📊 **تحليل الزوج:** {symbol_key}\n"
            f"⏱ **الفريم:** 5 دقائق (5m)\n"
            f"💵 **السعر الحالي:** {price}\n"
            f"🧱 **المقاومة القريبة:** {resistance}\n"
            f"🛡 **الدعم القريب:** {support}\n"
            f"📈 **الاتجاه:** {direction}\n\n"
            f"📉 **RSI (14):** {rsi}\n"
            f"-------------------------------\n"
            f"🎯 {signal}"
        )
        return msg
    except Exception as e:
        return f"⚠️ حدث خطأ أثناء التحليل: {e}"

def build_inline_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = [types.InlineKeyboardButton(text=pair, callback_data=pair) for pair in PAIRS.keys()]
    markup.add(*buttons)
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "أهلاً بك! اختر الزوج أو السهم للحصول على تحليل فني وتوصية تداول (5m):",
        reply_markup=build_inline_keyboard(),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data in PAIRS:
        bot.answer_callback_query(call.id, "جاري التحليل...")
        bot.send_message(call.message.chat.id, "⏳ جاري تحليل الزوج...")
        analysis = get_analysis(call.data)
        bot.send_message(
            call.message.chat.id, 
            analysis, 
            reply_markup=build_inline_keyboard(),
            parse_mode="Markdown"
        )

if __name__ == "__main__":
    try:
        bot.remove_webhook()
    except Exception:
        pass

    while True:
        try:
            bot.polling(none_stop=True, interval=2, timeout=30, skip_pending=True)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)
            
            
            
            
            
    
                



            





    
    
    
    
    
    
    
    
    
    
    
