import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yfinance as yf
import pandas as pd

# 1. إعداد التوكن والربط مع تليجرام
BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# 2. قائمة أزواج العملات والذهب
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

# 3. دالة حساب RSI يدوياً
def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# 4. دالة التحليل الفني الموسعة (فريم 5 دقائق)
def analyze_forex_pair(symbol):
    try:
        # جلب بيانات فريم 5 دقائق لآخر 5 أيام لضمان دقة الحسابات
        df = yf.download(tickers=symbol, period="5d", interval="5m")
        if df.empty or len(df) < 35:
            return "❌ تعذر جلب بيانات كافية للسوق حالياً."

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close_prices = df['Close']

        # حساب المتوسطات المتحركة EMA
        df['EMA_Fast'] = close_prices.ewm(span=9, adjust=False).mean()
        df['EMA_Slow'] = close_prices.ewm(span=21, adjust=False).mean()

        # حساب مؤشر RSI
        df['RSI'] = calculate_rsi(close_prices, window=14)

        # حساب MACD
        ema12 = close_prices.ewm(span=12, adjust=False).mean()
        ema26 = close_prices.ewm(span=26, adjust=False).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

        # حساب بولنجر باندز Bollinger Bands
        df['SMA20'] = close_prices.rolling(window=20).mean()
        df['STD20'] = close_prices.rolling(window=20).std()
        df['BB_High'] = df['SMA20'] + (df['STD20'] * 2)
        df['BB_Low'] = df['SMA20'] - (df['STD20'] * 2)

        # قراءة الشمعة الأخيرة
        latest = df.iloc[-1]
        price = round(float(latest['Close']), 5)
        rsi_val = round(float(latest['RSI']), 2)

        # تقييم الإشارات والشروط
        buy_score = 0
        sell_score = 0

        # شرط EMA
        if latest['EMA_Fast'] > latest['EMA_Slow']: buy_score += 1
        else: sell_score += 1

        # شرط RSI
        if 50 < latest['RSI'] < 70: buy_score += 1
        elif 30 < latest['RSI'] < 50: sell_score += 1

        # شرط MACD
        if latest['MACD'] > latest['MACD_Signal']: buy_score += 1
        else: sell_score += 1

        # شرط Bollinger Bands
        if latest['Close'] <= latest['BB_Low']: buy_score += 1
        elif latest['Close'] >= latest['BB_High']: sell_score += 1

        # صياغة النتيجة بناءً على قوة الشروط
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
            f"⏱️ **الفريم:** 5 دقائق (5m)\n"
            f"💵 **السعر الحالي:** {price}\n"
            f"📈 **الاتجاه:** {trend}\n"
            f"📉 **RSI (14):** {rsi_val}\n"
            f"─────────────────\n"
            f"{signal}"
        )
    except Exception as e:
        return f"حدث خطأ أثناء التحليل: {e}"

# 5. بناء واجهة الأزرار التفاعلية
def get_main_keyboard():
    markup = InlineKeyboardMarkup(row_width=3)
    buttons = [InlineKeyboardButton(pair, callback_data=pair) for pair in PAIR_MAP.keys() if pair != "Gold (XAU/USD)"]
    markup.add(*buttons)
    markup.add(InlineKeyboardButton("Gold (XAU/USD)", callback_data="Gold (XAU/USD)"))
    return markup

# 6. معالجة أمر البداية /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 
        "🤖 **مرحباً بك في بوت الإشارات الفنية (فريم 5m)**\nاختر الزوج الذي تريد تحليله من القائمة أدناه:", 
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

# 7. معالجة الضغط على الأزرار
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

# 8. تشغيل الاستماع المستمر للرسائل
bot.infinity_polling(timeout=60, long_polling_timeout=60)
 bot.remove_webhook()
bot.infinity_polling(timeout=60, long_polling_timeout=60)





    
    
    
    
    
    
    
    
    
    
    
