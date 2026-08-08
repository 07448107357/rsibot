import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import yfinance as yf
import pandas as pd



# 1. تعريف البوت والتوكين في البداية
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)



@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    
    # قائمة الأزرار
    buttons = [
        # العملات الرئيسية والفرعية
        telebot.types.InlineKeyboardButton("EUR/USD 🇪🇺🇺🇸", callback_data="EURUSD"),
        telebot.types.InlineKeyboardButton("GBP/USD 🇬🇧🇺🇸", callback_data="GBPUSD"),
        telebot.types.InlineKeyboardButton("USD/JPY 🇺🇸🇯🇵", callback_data="USDJPY"),
        telebot.types.InlineKeyboardButton("USD/CAD 🇺🇸🇨🇦", callback_data="USDCAD"),
        telebot.types.InlineKeyboardButton("AUD/USD 🇦🇺🇺🇸", callback_data="AUDUSD"),
        telebot.types.InlineKeyboardButton("USD/CHF 🇺🇸🇨🇭", callback_data="USDCHF"),
        telebot.types.InlineKeyboardButton("NZD/USD 🇳🇿🇺🇸", callback_data="NZDUSD"),
        telebot.types.InlineKeyboardButton("EUR/GBP 🇪🇺🇬🇧", callback_data="EURGBP"),
        telebot.types.InlineKeyboardButton("EUR/JPY 🇪🇺🇯🇵", callback_data="EURJPY"),
        telebot.types.InlineKeyboardButton("GBP/JPY 🇬🇧🇯🇵", callback_data="GBPJPY"),
        telebot.types.InlineKeyboardButton("EUR/CAD 🇪🇺🇨🇦", callback_data="EURCAD"),
        telebot.types.InlineKeyboardButton("EUR/AUD 🇪🇺🇦🇺", callback_data="EURAUD"),
        telebot.types.InlineKeyboardButton("EUR/CHF 🇪🇺🇨🇭", callback_data="EURCHF"),
        telebot.types.InlineKeyboardButton("GBP/CAD 🇬🇧🇨🇦", callback_data="GBPCAD"),
        telebot.types.InlineKeyboardButton("GBP/AUD 🇬🇧🇦🇺", callback_data="GBPAUD"),
        telebot.types.InlineKeyboardButton("GBP/CHF 🇬🇧🇨🇭", callback_data="GBPCHF"),
        telebot.types.InlineKeyboardButton("AUD/CAD 🇦🇺🇨🇦", callback_data="AUDCAD"),
        telebot.types.InlineKeyboardButton("AUD/JPY 🇦🇺🇯🇵", callback_data="AUDJPY"),
        telebot.types.InlineKeyboardButton("AUD/NZD 🇦🇺🇳🇿", callback_data="AUDNZD"),
        telebot.types.InlineKeyboardButton("NZD/JPY 🇳🇿🇯🇵", callback_data="NZDJPY"),
        telebot.types.InlineKeyboardButton("CAD/JPY 🇨🇦🇯🇵", callback_data="CADJPY"),
        telebot.types.InlineKeyboardButton("CHF/JPY 🇨🇭🇯🇵", callback_data="CHFJPY"),
        
        # المعادن والسلع
        telebot.types.InlineKeyboardButton("الذهب (Gold) 🥇", callback_data="XAUUSD"),
        telebot.types.InlineKeyboardButton("الفضة (Silver) 🥈", callback_data="XAGUSD"),
        telebot.types.InlineKeyboardButton("النفط (Crude Oil) 🛢️", callback_data="CL"),
        
        # العملات الرقمية
        telebot.types.InlineKeyboardButton("Bitcoin ₿", callback_data="BTC"),
        telebot.types.InlineKeyboardButton("Ethereum 💎", callback_data="ETH"),
        telebot.types.InlineKeyboardButton("Solana 🟣", callback_data="SOL"),
        telebot.types.InlineKeyboardButton("Binance Coin 🟡", callback_data="BNB"),
        telebot.types.InlineKeyboardButton("XRP 🚀", callback_data="XRP"),
        
        # الأسهم
        telebot.types.InlineKeyboardButton("Apple 🍏", callback_data="AAPL"),
        telebot.types.InlineKeyboardButton("Microsoft 💻", callback_data="MSFT"),
        telebot.types.InlineKeyboardButton("Google 🔍", callback_data="GOOGL"),
        telebot.types.InlineKeyboardButton("Amazon 📦", callback_data="AMZN"),
        telebot.types.InlineKeyboardButton("Tesla ⚡", callback_data="TSLA"),
        telebot.types.InlineKeyboardButton("Meta (Facebook) 🌐", callback_data="META"),
        telebot.types.InlineKeyboardButton("McDonald's 🍔", callback_data="MCD"),
        telebot.types.InlineKeyboardButton("Boeing ✈️", callback_data="BA"),
        telebot.types.InlineKeyboardButton("Intel 🖥️", callback_data="INTC")
    ]
    
    markup.add(*buttons)
    bot.send_message(message.chat.id, "اختر الأصل لتحليله واستخراج الإشارة:", reply_markup=markup)
    


# 3. دالة التحليل
# ---------------------------------------------------------
# خريطة الرموز الشاملة (أزواج، أسهم، عملات رقمية)
# ---------------------------------------------------------
SYMBOL_MAP = {
    # Forex
    "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "USDJPY": "JPY=X",
    "USDCAD": "CAD=X", "USDCHF": "CHF=X", "AUDUSD": "AUDUSD=X",
    "NZDUSD": "NZDUSD=X", "EURGBP": "EURGBP=X", "EURJPY": "EURJPY=X",
    "GBPJPY": "GBPJPY=X", "EURCAD": "EURCAD=X", "EURCHF": "EURCHF=X",
    "EURAUD": "EURAUD=X", "GBPCAD": "GBPCAD=X", "GBPCHF": "GBPCHF=X",
    "GBPAUD": "GBPAUD=X", "AUDCAD": "AUDCAD=X", "AUDJPY": "AUDJPY=X",
    "AUDNZD": "AUDNZD=X", "NZDJPY": "NZDJPY=X", "CADJPY": "CADJPY=X",
    "CHFJPY": "CHFJPY=X",
    # Commodities & Crypto
    "XAUUSD": "GC=F", "XAGUSD": "SI=F", "OIL": "CL=F",
    "BTC": "BTC-USD", "ETH": "ETH-USD", "SOL": "SOL-USD",
    "BNB": "BNB-USD", "XRP": "XRP-USD",
    # Stocks
    "AAPL": "AAPL", "MSFT": "MSFT", "GOOGL": "GOOGL",
    "AMZN": "AMZN", "TSLA": "TSLA", "META": "META",
    "MCD": "MCD", "BA": "BA", "INTC": "INTC"
}

# ---------------------------------------------------------
# دالة التحليل المحدثة
# ---------------------------------------------------------
def analyze_asset(ticker, interval="1m"):
    try:
        expiry_map = {
            "1m": "دقيقة واحدة (1m)",
            "5m": "5 دقائق (5m)",
            "15m": "15 دقيقة (15m)"
        }
        trade_duration = expiry_map.get(interval, "دقيقة واحدة")

        period = "5d" if interval in ["1m", "5m"] else "1mo"
        df = yf.download(tickers=ticker, period=period, interval=interval, progress=False)
        
        if df.empty or len(df) < 20:
            return f"⚠️ البيانات غير متوفرة حالياً للرمز {ticker} (قد يكون السوق مغلقاً)."

        if isinstance(df.columns, pd.MultiIndex):
            close = df['Close'][ticker].dropna()
            high = df['High'][ticker].dropna()
            low = df['Low'][ticker].dropna()
        else:
            close = df['Close'].dropna()
            high = df['High'].dropna()
            low = df['Low'].dropna()

        if len(close) < 20:
            return f"⚠️ عدد الشموع المتاحة غير كافٍ لتحليل {ticker}."

        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # Stochastic
        low_min = low.rolling(window=14).min()
        high_max = high.rolling(window=14).max()
        stoch_k = 100 * ((close - low_min) / (high_max - low_min))
        stoch_d = stoch_k.rolling(window=3).mean()

        # Moving Averages
        sma20 = close.rolling(window=20).mean()
        ema200 = close.ewm(span=200, adjust=False).mean()

        last_price = float(close.iloc[-1])
        last_rsi = float(rsi.fillna(50).iloc[-1])
        last_k = float(stoch_k.fillna(50).iloc[-1])
        last_d = float(stoch_d.fillna(50).iloc[-1])
        last_sma = float(sma20.fillna(last_price).iloc[-1])
        last_ema = float(ema200.fillna(last_price).iloc[-1])

        if last_rsi < 35 and last_k < 20:
            signal = "🟢 توصية: شراء قوية (CALL)"
        elif last_rsi > 65 and last_k > 80:
            signal = "🔴 توصية: بيع قوية (PUT)"
        elif last_rsi < 45:
            signal = "🟢 توصية: شراء خفيف (CALL)"
        elif last_rsi > 55:
            signal = "🔴 توصية: بيع خفيف (PUT)"
        else:
            signal = "⚪ لا توجد فرصة واضحة (انتظار)"

        direction = "اتجاه صاعد 📈" if last_price > last_ema else "اتجاه هابط 📉"

        return (
            f"📌 الرمز / Asset: {ticker}\n"
            f"⏱️ الإطار الزمني: {interval}\n"
            f"⏳ مدة الصفقة المقترحة: {trade_duration}\n\n"
            f"📊 تحليل السعر والمؤشرات:\n"
            f"💵 السعر الحالي: {last_price:.4f}\n"
            f"📈 RSI (14): {last_rsi:.2f}\n"
            f"📉 Stochastic (%K / %D): {last_k:.2f} / {last_d:.2f}\n"
            f"📊 SMA 20: {last_sma:.4f}\n"
            f"📊 EMA 200: {last_ema:.4f}\n\n"
            f"🎯 القرار:\n"
            f"{signal}\n"
            f"({direction})"
        )

    except Exception as e:
        return f"⚠️ حدث خطأ أثناء التحليل: {str(e)}"

# ---------------------------------------------------------
# دالة معالجة نقرات الأزرار
# ---------------------------------------------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if not call.message:
        return
        
    data = call.data
    bot.answer_callback_query(call.id, text="جاري المعالجة... ⏳")

    # 1. إذا تم اختيار أصول بها إطار زمني محدد (مثل EURUSD|5m)
    if "|" in data:
        asset, interval = data.split("|")
        ticker = SYMBOL_MAP.get(asset, asset)
        result = analyze_asset(ticker=ticker, interval=interval)
        bot.send_message(call.message.chat.id, result)

    # 2. إذا تم اختيار اسم الأصل فقط (إظهار أزرار اختيار الفريم)
    else:
        asset_key = data
        ticker = SYMBOL_MAP.get(asset_key, asset_key)
        
        markup = types.InlineKeyboardMarkup(row_width=3)
        btn_1m = types.InlineKeyboardButton("⏱️ 1 دقيقة", callback_data=f"{asset_key}|1m")
        btn_5m = types.InlineKeyboardButton("⏱️ 5 دقائق", callback_data=f"{asset_key}|5m")
        btn_15m = types.InlineKeyboardButton("⏱️ 15 دقيقة", callback_data=f"{asset_key}|15m")
        markup.add(btn_1m, btn_5m, btn_15m)

        bot.send_message(
            call.message.chat.id, 
            f"اختر الإطار الزمني لتحليل **{asset_key}**:", 
            reply_markup=markup,
            parse_mode="Markdown"
        )
        
            
            
        
            




# 4. أوامر البوت
@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [KeyboardButton(text) for text in ASSETS.keys()]
    markup.add(*buttons)
    bot.reply_to(message, "📋 اختر الأصل لتحليله واستخراج الإشارة:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ASSETS)
def handle_asset_selection(message):
    asset_name = message.text
    symbol = ASSETS[asset_name]
    
    bot.reply_to(message, f"⏳ جاري جلب البيانات وتحليل {asset_name}...")
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="7d", interval="15m")
        
        if df.empty:
            bot.reply_to(message, "❌ تعذر جلب بيانات هذا الأصل حالياً، يرجى المحاولة لاحقاً.")
            return

        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        last_rsi = round(df['RSI'].iloc[-1], 2)
        last_price = round(df['Close'].iloc[-1], 4)
        
        if last_rsi >= 70:
            signal = "🔴 **إشارة بيع (Overbought)** - السوق في منطقة تشبع شرائي."
        elif last_rsi <= 30:
            signal = "🟢 **إشارة شراء (Oversold)** - السوق في منطقة تشبع بيعي."
        else:
            signal = "⚪ **حالة محايدة (Neutral)** - لا توجد إشارة واضحة حالياً."
            
        response_text = (
            f"📊 **نتيجة تحليل {asset_name}:**\n\n"
            f"💵 السعر الحالي: `{last_price}`\n"
            f"📈 قيمة RSI (14): `{last_rsi}`\n\n"
            f"🎯 **التوصية:**\n{signal}"
        )
        
        bot.send_message(message.chat.id, response_text, parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, f"⚠️ حدث خطأ أثناء التحليل: {str(e)}")
        
    bot.reply_to(message, f"⏳ جاري جلب البيانات وتحليل {asset_name}...")
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="7d", interval="15m")
        
        if df.empty:
            bot.reply_to(message, "❌ تعذر جلب بيانات هذا الأصل حالياً، يرجى المحاولة لاحقاً.")
            return

        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        last_rsi = round(df['RSI'].iloc[-1], 2)
        last_price = round(df['Close'].iloc[-1], 4)
        
        if last_rsi >= 70:
            signal = "🔴 **إشارة بيع (Overbought)** - السوق في منطقة تشبع شرائي."
        elif last_rsi <= 30:
            signal = "🟢 **إشارة شراء (Oversold)** - السوق في منطقة تشبع بيعي."
        else:
            signal = "⚪ **حالة محايدة (Neutral)** - لا توجد إشارة واضحة حالياً."
            
        response_text = (
            f"📊 **نتيجة تحليل {asset_name}:**\n\n"
            f"💵 السعر الحالي: `{last_price}`\n"
            f"📈 قيمة RSI (14): `{last_rsi}`\n\n"
            f"🎯 **التوصية:**\n{signal}"
        )
        
        bot.send_message(message.chat.id, response_text, parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, f"⚠️ حدث خطأ أثناء التحليل: {str(e)}")

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    
    # قائمة الأزرار
    btn1 = telebot.types.InlineKeyboardButton("EUR/USD 🇪🇺🇺🇸", callback_data="EURUSD")
    btn2 = telebot.types.InlineKeyboardButton("GBP/USD 🇬🇧🇺🇸", callback_data="GBPUSD")
    btn3 = telebot.types.InlineKeyboardButton("الذهب (Gold) 🥇", callback_data="XAUUSD")
    btn4 = telebot.types.InlineKeyboardButton("USD/JPY 🇺🇸🇯🇵", callback_data="USDJPY")
    
    markup.add(btn1, btn2, btn3, btn4)
    
    # إرسال الرسالة مع الأزرار
    bot.send_message(message.chat.id, "اختر الأصل لتحليله واستخراج الإشارة:", reply_markup=markup)
    
    
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.message:
        data = call.data
        
        if "|" in data:
            # إزالة استجابة الزر فوراً لمنع التكرار والنقر المزدوج
            bot.answer_callback_query(call.id, text="جاري التحليل... برجاء الانتظار ⏳")
            
            asset, interval = data.split("|")
            
            symbol_map = {
                "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "USDJPY": "JPY=X",
                "USDCAD": "CAD=X", "USDCHF": "CHF=X", "AUDUSD": "AUDUSD=X",
                "NZDUSD": "NZDUSD=X", "EURGBP": "EURGBP=X", "EURJPY": "EURJPY=X",
                "GBPJPY": "GBPJPY=X", "EURCAD": "EURCAD=X", "EURCHF": "EURCHF=X",
                "EURAUD": "EURAUD=X", "GBPCAD": "GBPCAD=X", "GBPCHF": "GBPCHF=X",
                "GBPAUD": "GBPAUD=X", "AUDCAD": "AUDCAD=X", "AUDJPY": "AUDJPY=X",
                "AUDNZD": "AUDNZD=X", "NZDJPY": "NZDJPY=X", "CADJPY": "CADJPY=X",
                "CHFJPY": "CHFJPY=X", "XAUUSD": "GC=F", "XAGUSD": "SI=F",
                "BTC": "BTC-USD", "ETH": "ETH-USD"
            }
            
            ticker = symbol_map.get(asset, asset)
            
            try:
                result = analyze_asset(ticker=ticker, interval=interval)
                bot.send_message(call.message.chat.id, result)
            except Exception as e:
                bot.send_message(call.message.chat.id, f"⚠️ حدث خطأ أثناء التحليل: {str(e)}")
                
                

        # إذا قام المستخدم باختيار الزوج فقط، نعرض له أزرار الفريمات الزمنية
        else:
            markup = telebot.types.InlineKeyboardMarkup(row_width=3)
            btn1 = telebot.types.InlineKeyboardButton("⏱️ 1 دقيقة", callback_data=f"{data}|1m")
            btn2 = telebot.types.InlineKeyboardButton("⏱️ 5 دقائق", callback_data=f"{data}|5m")
            btn3 = telebot.types.InlineKeyboardButton("⏱️ 15 دقيقة", callback_data=f"{data}|15m")
            markup.add(btn1, btn2, btn3)
            
            bot.send_message(call.message.chat.id, f"اختر الإطار الزمني لـ {data}:", reply_markup=markup)
            
        
        try:
            response_text = analyze_asset(ticker)
            bot.send_message(call.message.chat.id, response_text, parse_mode="Markdown")
        except Exception as e:
            bot.send_message(call.message.chat.id, f"⚠️ حدث خطأ أثناء التحليل: {e}")
            
        
# تشغيل البوت
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling(timeout=60, long_polling_timeout=1)
    
