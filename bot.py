import os
import telebot
import yfinance as yf
import pandas as pd
from telebot import types

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

PAIRS = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "AUD/USD": "AUDUSD=X",
    "USD/JPY": "USDJPY=X",
    "USD/CHF": "USDCHF=X",
    "USD/CAD": "USDCAD=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X",
    "Gold (XAU/USD)": "GC=F"
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
            return "❌ تعذر جلب البيانات الكافية لهذا الزوج حالياً."
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close_prices = df['Close']
        high_prices = df['High']
        low_prices = df['Low']

        # حساب المتوسطات
        df['EMA_Fast'] = close_prices.ewm(span=9, adjust=False).mean()
        df['EMA_Slow'] = close_prices.ewm(span=21, adjust=False).mean()

        # حساب RSI
        df['RSI'] = calculate_rsi(close_prices, 14)

        # حساب MACD
        ema12 = close_prices.ewm(span=12, adjust=False).mean()
        ema26 = close_prices.ewm(span=26, adjust=False).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

        # حساب Bollinger Bands
        df['SMA20'] = close_prices.rolling(window=20).mean()
        df['STD20'] = close_prices.rolling(window=20).std()
        df['BB_High'] = df['SMA20'] + (df['STD20'] * 2)
        df['BB_Low'] = df['SMA20'] - (df['STD20'] * 2)

        last_row = df.iloc[-1]
        price = round(float(last_row['Close']), 2)
        rsi_val = round(float(last_row['RSI']), 2)
        
        # حساب الدعم والمقاومة
        support_level = float(low_prices.tail(20).min())
        resistance_level = float(high_prices.tail(20).max())

        near_support = abs(price - support_level) / price < 0.001
        near_resistance = abs(price - resistance_level) / price < 0.001

        # نظام النقاط للتوصية
        buy_score = 0
        sell_score = 0

        if rsi_val < 35: buy_score += 1
        elif rsi_val > 65: sell_score += 1

        if last_row['EMA_Fast'] > last_row['EMA_Slow']: buy_score += 1
        elif last_row['EMA_Fast'] < last_row['EMA_Slow']: sell_score += 1

        if last_row['MACD'] > last_row['MACD_Signal']: buy_score += 1
        elif last_row['MACD'] < last_row['MACD_Signal']: sell_score += 1

        if price <= last_row['BB_Low']: buy_score += 1
        elif price >= last_row['BB_High']: sell_score += 1

        # إعداد التوصية والتنبيه مع الدعم والمقاومة
        if buy_score >= 2 and buy_score > sell_score:
            if near_resistance:
                trend = "صاعد لكن قرب مقاومة ⚠️"
                signal = "🟢 **BUY SIGNAL (CALL / UP)**\n⚠️ *تنبيه: السعر قريب من المقاومة!*"
            else:
                trend = "صاعد ⬆️"
                signal = "🟢 **BUY SIGNAL (CALL / UP)**"

        elif sell_score >= 2 and sell_score > buy_score:
            if near_support:
                trend = "هابط لكن قرب دعم ⚠️"
                signal = "🔴 **SELL SIGNAL (PUT / DOWN)**\n⚠️ *تنبيه: السعر قريب من الدعم!*"
            else:
                trend = "هابط ⬇️"
                signal = "🔴 **SELL SIGNAL (PUT / DOWN)**"

        else:
            trend = "متذبذب ⚖️"
            signal = "⚪ **السوق غير واضح (انتظر فرصة أفضل)**"

        clean_symbol = symbol_key

        return (
            f"📊 **تحليل الزوج:** {clean_symbol}\n"
            f"⏱️ **الفريم:** 5 دقائق (5m)\n"
            f"💵 **السعر الحالي:** {price}\n"
            f"🧱 **المقاومة القريبة:** {round(resistance_level, 2)}\n"
            f"🛡️ **الدعم القريب:** {round(support_level, 2)}\n"
            f"📈 **الاتجاه:** {trend}\n"
            f"📉 **RSI (14):** {rsi_val}\n"
            f"-----------------------------------\n"
            f"{signal}"
        )

    except Exception as e:
        return f"⚠️ حدث خطأ أثناء التحليل: {e}"

def build_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    buttons = [types.KeyboardButton(pair) for pair in PAIRS.keys()]
    markup.add(*buttons)
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(
        message,
        "أهلاً بك! اختر الزوج للحصول على تحليل فني وتوصية تداول (5m):",
        reply_markup=build_keyboard()
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text in PAIRS:
        bot.send_message(message.chat.id, "⏳ جاري تحليل السوق...")
        analysis = get_analysis(message.text)
        bot.send_message(message.chat.id, analysis, parse_mode="Markdown", reply_markup=build_keyboard())
    else:
        bot.send_message(message.chat.id, "الرجاء اختيار زوج من القائمة أدناه.", reply_markup=build_keyboard())

if __name__ == "__main__":
    import time
    
    # حذف أي Webhook قديم أو اتصالات معلقة
    try:
        bot.remove_webhook()
    except Exception as e:
        print(f"Webhook cleanup note: {e}")

    # إعادة المحاولة تلقائياً عند حدوث التعارض (Conflict)
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=20, skip_pending=True)
        except Exception as e:
            print(f"Error occurred: {e}")
            time.sleep(3)  # الانتظار 3 ثوانٍ قبل إعادة المحاولة لتفريغ الجلسة القديمة
            
    
                



            





    
    
    
    
    
    
    
    
    
    
    
