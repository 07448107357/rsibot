import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yfinance as yf
import pandas as pd
import ta

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

PAIR_MAP = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "AUD/USD": "AUDUSD=X",
    "USD/JPY": "JPY=X",
    "USD/CHF": "CHF=X",
    "USD/CAD": "CAD=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X",
    "Gold (XAU/USD)": "GC=F"
}

def analyze_forex_pair(symbol):
    try:
        # جلب البيانات لآخر يوم بفريم 5 دقائق
        data = yf.download(tickers=symbol, period="1d", interval="5m")
        if data.empty:
            return "❌ تعذر جلب بيانات السوق حالياً."

        df = data.copy()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # 1. المتوسطات المتحركة للاتجاه (EMA)
        df['EMA_Fast'] = ta.trend.ema_indicator(df['Close'], window=9)
        df['EMA_Slow'] = ta.trend.ema_indicator(df['Close'], window=21)
        
        # 2. مؤشر القوة النسبية (RSI)
        df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
        
        # 3. مؤشر MACD
        macd = ta.trend.MACD(df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        
        # 4. بولنجر باندز (Bollinger Bands)
        bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
        df['BB_High'] = bb.bollinger_hband()
        df['BB_Low'] = bb.bollinger_lband()

        latest = df.iloc[-1]
        price = round(float(latest['Close']), 5)
        rsi_val = round(float(latest['RSI']), 2)

        # حساب النقاط لتحديد قوة الإشارة
        buy_score = 0
        sell_score = 0

        # فحص الشروط
        if latest['EMA_Fast'] > latest['EMA_Slow']: buy_score += 1
        else: sell_score += 1

        if 50 < latest['RSI'] < 70: buy_score += 1
        elif 30 < latest['RSI'] < 50: sell_score += 1

        if latest['MACD'] > latest['MACD_Signal']: buy_score += 1
        else: sell_score += 1

        if latest['Close'] <= latest['BB_Low']: buy_score += 1
        elif latest['Close'] >= latest['BB_High']: sell_score += 1

        # صياغة النتيجة حسب قوة النقاط
        if buy_score >= 3:
            trend = "صاعد قوي ⬆️"
            signal = f"🟢 **BUY SIGNAL (CALL / UP)**\n🎯 نسبة التوافق: {buy_score * 25}%"
        elif sell_score >= 3:
            trend = "هابط قوي ⬇️"
            signal = f"🔴 **SELL SIGNAL (PUT / DOWN)**\n🎯 نسبة التوافق: {sell_score * 25}%"
        else:
            trend = "متذبذب ⚖️"
            signal = "⚪ **السوق غير واضح (انتظر فرصة أفضل)**"

        return (
            f"📊 **تحليل الزوج:** {symbol}\n"
            f"💵 **السعر الحالي:** {price}\n"
            f"📈 **الاتجاه:** {trend}\n"
            f"📉 **RSI (14):** {rsi_val}\n"
            f"─────────────────\n"
            f"{signal}"
        )
    except Exception as e:
        return f"حدث خطأ أثناء التحليل: {e}"

def get_main_keyboard():
    markup = InlineKeyboardMarkup(row_width=3)
    buttons = [InlineKeyboardButton(pair, callback_data=pair) for pair in PAIR_MAP.keys() if pair != "Gold (XAU/USD)"]
    markup.add(*buttons)
    markup.add(InlineKeyboardButton("Gold (XAU/USD)", callback_data="Gold (XAU/USD)"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 
        "🤖 **مرحباً بك في بوت الإشارات الفنية**\nاختر الزوج الذي تريد تحليله من القائمة أدناه:", 
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    symbol_key = call.data
    if symbol_key in PAIR_MAP:
        bot.answer_callback_query(call.id, f"جاري تحليل {symbol_key}...")
        ticker = PAIR_MAP[symbol_key]
        result = analyze_forex_pair(ticker)
        
        bot.send_message(
            call.message.chat.id, 
            result, 
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

bot.bot.infinity_polling(timeout=60, long_polling_timeout=60)




    
    
    
    
    
    
    
    
    
    
    
