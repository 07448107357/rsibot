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
def analyze_asset(ticker, interval="1m"):
    try:
        # تحديد فترة جلب البيانات بناءً على الفريم الزمني
        period = "1d" if interval in ["1m", "5m", "15m"] else "5d"
        
        # جلب البيانات
        df = yf.download(tickers=ticker, period=period, interval=interval, progress=False)
        
        if df.empty or len(df) < 14:
            return f"⚠️ البيانات غير كافية لتحليل الرمز {ticker} على فريم {interval}."

        # معالجة تنسيق البيانات من yfinance
        if isinstance(df.columns, pd.MultiIndex):
            close = df['Close'][ticker]
            high = df['High'][ticker]
            low = df['Low'][ticker]
        else:
            close = df['Close']
            high = df['High']
            low = df['Low']

        current_price = float(close.iloc[-1])

        # 1. حساب مؤشر RSI (14)
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = float(rsi.iloc[-1])

        # 2. حساب مؤشر Stochastic (14, 3, 3)
        low_14 = low.rolling(window=14).min()
        high_14 = high.rolling(window=14).max()
        stoch_k = 100 * ((close - low_14) / (high_14 - low_14))
        stoch_d = stoch_k.rolling(window=3).mean()
        current_k = float(stoch_k.iloc[-1])
        current_d = float(stoch_d.iloc[-1])

        # 3. حساب المتوسطات المتحركة SMA 20 & EMA 200
        sma_20 = float(close.rolling(window=20).mean().iloc[-1]) if len(close) >= 20 else current_price
        ema_200 = float(close.ewm(span=200, adjust=False).mean().iloc[-1]) if len(close) >= 200 else current_price

        # اتخاذ القرار الإشاري
        if current_rsi < 30 and current_k < 20:
            decision = "🟢 توصية: شراء (CALL)\n(تشبع بيعي - صعود متوقع)"
        elif current_rsi > 70 and current_k > 80:
            decision = "🔴 توصية: بيع (PUT)\n(تشبع شرائي - هبوط متوقع)"
        elif current_price > sma_20:
            decision = "🟢 توصية: شراء (CALL)\n(اتجاه صاعد)"
        else:
            decision = "🔴 توصية: بيع (PUT)\n(اتجاه هابط)"

        # صياغة النتيجة
        response = (
            f"📌 الرمز / Asset: {ticker}\n"
            f"⏱️ الإطار الزمني: {interval}\n\n"
            f"📊 تحليل السعر والمؤشرات:\n"
            f"💵 السعر الحالي: {current_price:.4f}\n"
            f"📈 RSI (14): {current_rsi:.2f}\n"
            f"📉 Stochastic (%K / %D): {current_k:.2f} / {current_d:.2f}\n"
            f"📊 SMA 20: {sma_20:.4f}\n"
            f"📊 EMA 200: {ema_200:.4f}\n\n"
            f"🎯 القرار:\n{decision}"
        )
        return response

    except Exception as e:
        return f"⚠️ حدث خطأ أثناء تحليل الرمز {ticker}: {str(e)}"
        
            




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
        
        # إذا كان الخيار يحتوي على الفريم الزمني (مثل: EURUSD|1m)
        if "|" in data:
            asset, interval = data.split("|")
            bot.answer_callback_query(call.id, text=f"جاري التحليل لفريم {interval}...")
            
            symbol_map = {
                # أزواج العملات
                "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "USDJPY": "JPY=X",
                "USDCAD": "CAD=X", "AUDUSD": "AUDUSD=X", "USDCHF": "CHF=X",
                "NZDUSD": "NZDUSD=X", "EURGBP": "EURGBP=X", "EURJPY": "EURJPY=X",
                "GBPJPY": "GBPJPY=X", "EURCAD": "EURCAD=X", "EURAUD": "EURAUD=X",
                "EURCHF": "EURCHF=X", "GBPCAD": "GBPCAD=X", "GBPAUD": "GBPAUD=X",
                "GBPCHF": "GBPCHF=X", "AUDCAD": "AUDCAD=X", "AUDJPY": "AUDJPY=X",
                "AUDNZD": "AUDNZD=X", "NZDJPY": "NZDJPY=X", "CADJPY": "CADJPY=X",
                "CHFJPY": "CHFJPY=X",
                
                # المعادن والسلع
                "XAUUSD": "GC=F", "XAGUSD": "SI=F", "CL": "CL=F",
                
                # العملات الرقمية
                "BTC": "BTC-USD", "ETH": "ETH-USD", "SOL": "SOL-USD",
                "BNB": "BNB-USD", "XRP": "XRP-USD",
                
                # الأسهم العالمية
                "AAPL": "AAPL", "MSFT": "MSFT", "GOOGL": "GOOGL",
                "AMZN": "AMZN", "TSLA": "TSLA", "META": "META",
                "MCD": "MCD", "BA": "BA", "INTC": "INTC"
            }
            
            ticker = symbol_map.get(asset, asset)
            
            try:
                response_text = analyze_asset(ticker, interval=interval)
                bot.send_message(call.message.chat.id, response_text)
            except Exception as e:
                bot.send_message(call.message.chat.id, f"حدث خطأ أثناء التحليل: {e}")

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
    
