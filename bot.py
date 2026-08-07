import os
import telebot
import yfinance as yf
import pandas as pd

# 1. تعريف البوت والتوكين في البداية
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)


# 2. قائمة الأصول
ASSETS = {
    "EUR/USD 🇪🇺🇺🇸": "EURUSD=X",
    "GBP/USD 🇬🇧🇺🇸": "GBPUSD=X",
    "USD/JPY 🇺🇸🇯🇵": "JPY=X",
    "AUD/USD 🇦🇺🇺🇸": "AUDUSD=X",
    "USD/CAD 🇺🇸🇨🇦": "CAD=X",
    "USD/CHF 🇺🇸🇨🇭": "CHF=X",
    "الذهب (Gold) 🥇": "GC=F",
    "الفضة (Silver) 🥈": "SI=F",
    "بيتكوين (Bitcoin) ₿": "BTC-USD",
    "إيثيريوم (Ethereum) 💎": "ETH-USD",
    "Apple 🍎": "AAPL",
    "Amazon 📦": "AMZN",
    "McDonald's 🍔": "MCD",
    "Meta (Facebook) 🌐": "META",
    "Google 🔍": "GOOGL",
    "Tesla ⚡": "TSLA",
    "Microsoft 💻": "MSFT",
    "Boeing ✈️": "BA",
    "Intel 💻": "INTC"
}

# 3. دالة التحليل
def analyze_asset(ticker_symbol):
    try:
        # جلب البيانات بفاصل 5 دقائق
        df = yf.download(tickers=ticker_symbol, period="5d", interval="5m")
        
        if df.empty or len(df) < 20:
            return "❌ لا توجد بيانات كافية للتحليل حالياً."

        # حساب المؤشرات
        df['SMA20'] = df['Close'].rolling(window=20).mean()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()

        # حساب Stochastic
        low_min = df['Low'].rolling(window=14).min()
        high_max = df['High'].rolling(window=14).max()
        df['%K'] = 100 * ((df['Close'] - low_min) / (high_max - low_min))
        df['%D'] = df['%K'].rolling(window=3).mean()

        # حساب RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # استخراج آخر القيم باستخدام .item() لمنع خطأ Series
        last_price = float(df['Close'].iloc[-1].item())
        last_rsi = float(df['RSI'].iloc[-1].item())
        last_k = float(df['%K'].iloc[-1].item())
        last_d = float(df['%D'].iloc[-1].item())
        last_sma = float(df['SMA20'].iloc[-1].item())
        last_ema = float(df['EMA200'].iloc[-1].item())

        # صياغة رسالة التحليل
        analysis = (
            f"📊 **تحليل السعر والمؤشرات:**\n\n"
            f"💵 **السعر الحالي:** `{last_price:.4f}`\n"
            f"📈 **RSI (14):** `{last_rsi:.2f}`\n"
            f"📉 **Stochastic (%K / %D):** `{last_k:.2f}` / `{last_d:.2f}`\n"
            f"📊 **SMA 20:** `{last_sma:.4f}`\n"
            f"📊 **EMA 200:** `{last_ema:.4f}`\n"
        )
        return analysis

    except Exception as e:
        return f"⚠️ حدث خطأ أثناء التحليل: {str(e)}"
        
                # جلب البيانات مباشرة لمتغير df
        df = yf.download(tickers=ticker_symbol, period="5d", interval="5m")
        
        if df.empty or len(df) < 20:
            return "❌ لا توجد بيانات كافية للتحليل حالياً."
            

        df['SMA20'] = df['Close'].rolling(window=20).mean()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()

        low_min = df['Low'].rolling(window=14).min()
        high_max = df['High'].rolling(window=14).max()
        df['%K'] = 100 * ((df['Close'] - low_min) / (high_max - low_min))
        df['%D'] = df['%K'].rolling(window=3).mean()

        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        price = round(float(df['Close'].iloc[-1]), 4)
        sma = float(df['SMA20'].iloc[-1])
        ema200 = float(df['EMA200'].iloc[-1])
        stoch_k = round(float(df['%K'].iloc[-1]), 2)
        stoch_d = round(float(df['%D'].iloc[-1]), 2)
        rsi = round(float(df['RSI'].iloc[-1]), 2)

        if price > ema200 and price > sma:
            direction = "🟢 صاعد قوي ⬆️"
        elif price < ema200 and price < sma:
            direction = "🔴 هابط قوي ⬇️"
        else:
            direction = "🟡 عرضي / متذبذب 🔄"

        if price > ema200 and rsi < 40 and stoch_k < 30:
            signal = "🟢 **توصية شراء قوية (BUY 🟢)**"
        elif price < ema200 and rsi > 60 and stoch_k > 70:
            signal = "🔴 **توصية بيع قوية (SELL 🔴)**"
        else:
            signal = "⚪ **انتظار / لا توجد فرصة واضحة**"

        return (
            f"📊 **تحليل الأصل:** `{ticker_symbol}`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💵 **السعر الحالي:** `${price}`\n"
            f"📈 **الاتجاه العام:** {direction}\n"
            f"🎯 **الإشارة:** {signal}\n\n"
            f"🔹 **مؤشر RSI:** `{rsi}`\n"
            f"🔹 **Stochastic %K:** `{stoch_k}`\n"
            f"🔹 **Stochastic %D:** `{stoch_d}`\n"
            f"━━━━━━━━━━━━━━━━━━"
        )
    except Exception as e:
        return f"⚠️ حدث خطأ أثناء التحليل: {str(e)}"

# 4. أوامر البوت
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "👋 أهلاً بك! البوت جاهز لتحليل العملات والأسهم. أرسل /menu لعرض القائمة.")

@bot.message_handler(commands=['menu'])
def show_menu(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for name, symbol in ASSETS.items():
        buttons.append(telebot.types.InlineKeyboardButton(text=name, callback_data=symbol))
    markup.add(*buttons)
    bot.reply_to(message, "📋 **اختر الأصل لتحليله واستخرج الإشارة:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    bot.answer_callback_query(call.id, "جاري تحليل الأصل...")
    result = analyze_asset(call.data)
    bot.send_message(call.message.chat.id, result, parse_mode="Markdown")
    


# 5. تشغيل البوت في النهاية فقط
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
    
    
    

            
            
            
            
            
    
                



            





    
    
    
    
    
    
    
    
    
    
    
