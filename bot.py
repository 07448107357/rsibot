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

        # استخراج آخر القيم
        last_price = float(df['Close'].iloc[-1].item())
        last_rsi = float(df['RSI'].iloc[-1].item())
        last_k = float(df['%K'].iloc[-1].item())
        last_d = float(df['%D'].iloc[-1].item())
        last_sma = float(df['SMA20'].iloc[-1].item())
        last_ema = float(df['EMA200'].iloc[-1].item())

        # منطق تحديد التوصية
        if last_rsi < 45 and last_k < 45:
            signal = "🟢 **توصية: شراء (CALL)** \n*(اتجاه هابط قادم للارتداد)*"
        elif last_rsi > 55 and last_k > 55:
            signal = "🔴 **توصية: بيع (PUT)** \n*(اتجاه صاعد قادم للهبوط)*"
        elif last_rsi <= 50:
            signal = "🟢 **توصية: شراء خفيف**"
        else:
            signal = "🔴 **توصية: بيع خفيف**"

        # صياغة رسالة التحليل وتضمين الرمز
        analysis = (
            f"📌 **الرمز / Asset:** `{ticker_symbol}`\n\n"
            f"📊 **تحليل السعر والمؤشرات:**\n"
            f"💵 **السعر الحالي:** `{last_price:.4f}`\n"
            f"📈 **RSI (14):** `{last_rsi:.2f}`\n"
            f"📉 **Stochastic (%K / %D):** `{last_k:.2f}` / `{last_d:.2f}`\n"
            f"📊 **SMA 20:** `{last_sma:.4f}`\n"
            f"📊 **EMA 200:** `{last_ema:.4f}`\n\n"
            f"🎯 **القرار:**\n{signal}"
        )
        return analysis

    except Exception as e:
        return f"⚠️ حدث خطأ أثناء التحليل: {str(e)}"
        
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

        # استخراج آخر القيم
        last_price = float(df['Close'].iloc[-1].item())
        last_rsi = float(df['RSI'].iloc[-1].item())
        last_k = float(df['%K'].iloc[-1].item())
        last_d = float(df['%D'].iloc[-1].item())
        last_sma = float(df['SMA20'].iloc[-1].item())
        last_ema = float(df['EMA200'].iloc[-1].item())

        # منطق تحديد التوصية
        if last_rsi < 45 and last_k < 45:
            signal = "🟢 **توصية: شراء (CALL)** \n*(اتجاه هابط قادم للارتداد)*"
        elif last_rsi > 55 and last_k > 55:
            signal = "🔴 **توصية: بيع (PUT)** \n*(اتجاه صاعد قادم للهبوط)*"
        elif last_rsi <= 50:
            signal = "🟢 **توصية: شراء خفيف**"
        else:
            signal = "🔴 **توصية: بيع خفيف**"

        # صياغة رسالة التحليل مع إظهار اسم الأصل والرمز
        analysis = (
            f"📌 **الزوج / الأصل:** {asset_name} (`{ticker_symbol}`)\n\n"
            f"📊 **تحليل السعر والمؤشرات:**\n"
            f"💵 **السعر الحالي:** `{last_price:.4f}`\n"
            f"📈 **RSI (14):** `{last_rsi:.2f}`\n"
            f"📉 **Stochastic (%K / %D):** `{last_k:.2f}` / `{last_d:.2f}`\n"
            f"📊 **SMA 20:** `{last_sma:.4f}`\n"
            f"📊 **EMA 200:** `{last_ema:.4f}`\n\n"
            f"🎯 **القرار:**\n{signal}"
        )
        return analysis

    except Exception as e:
        return f"⚠️ حدث خطأ أثناء التحليل: {str(e)}"
        
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

        # استخراج آخر القيم
        last_price = float(df['Close'].iloc[-1].item())
        last_rsi = float(df['RSI'].iloc[-1].item())
        last_k = float(df['%K'].iloc[-1].item())
        last_d = float(df['%D'].iloc[-1].item())
        last_sma = float(df['SMA20'].iloc[-1].item())
        last_ema = float(df['EMA200'].iloc[-1].item())

        # منطق تحديد التوصية بصورة مرنة
        if last_rsi < 45 and last_k < 45:
            signal = "🟢 **توصية: شراء (CALL)** \n*(اتجاه هابط قادم للارتداد)*"
        elif last_rsi > 55 and last_k > 55:
            signal = "🔴 **توصية: بيع (PUT)** \n*(اتجاه صاعد قادم للهبوط)*"
        elif last_rsi <= 50:
            signal = "🟢 **توصية: شراء خفيف**"
        else:
            signal = "🔴 **توصية: بيع خفيف**"

        # صياغة رسالة التحليل مع إضافة اسم الأصل/الزوج
        analysis = (
            f"📌 **الزوج / الأصل:** `{ticker_symbol}`\n\n"
            f"📊 **تحليل السعر والمؤشرات:**\n"
            f"💵 **السعر الحالي:** `{last_price:.4f}`\n"
            f"📈 **RSI (14):** `{last_rsi:.2f}`\n"
            f"📉 **Stochastic (%K / %D):** `{last_k:.2f}` / `{last_d:.2f}`\n"
            f"📊 **SMA 20:** `{last_sma:.4f}`\n"
            f"📊 **EMA 200:** `{last_ema:.4f}`\n\n"
            f"🎯 **القرار:**\n{signal}"
        )
        return analysis

    except Exception as e:
        return f"⚠️ حدث خطأ أثناء التحليل: {str(e)}"
        
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

        # استخراج آخر القيم
        last_price = float(df['Close'].iloc[-1].item())
        last_rsi = float(df['RSI'].iloc[-1].item())
        last_k = float(df['%K'].iloc[-1].item())
        last_d = float(df['%D'].iloc[-1].item())
        last_sma = float(df['SMA20'].iloc[-1].item())
        last_ema = float(df['EMA200'].iloc[-1].item())

        # منطق تحديد التوصية بصورة مرنة
        if last_rsi < 35 and last_k < 20:
            signal = "🟢 **توصية: شراء (CALL)** \n*(تشبع بيعي قوي)*"
        elif last_rsi > 65 and last_k > 80 and last_k < last_d:
            signal = "🔴 **توصية: بيع (PUT)** \n*(تأكيد بداية الارتداد للهبوط)*"
        elif last_rsi <= 48:
            signal = "🟢 **توصية: شراء خفيف**"
        elif last_rsi >= 52:
            signal = "🔴 **توصية: بيع خفيف**"
        else:
            signal = "⚪ **حالة حيادية: انتظار**"
            

        # صياغة رسالة التحليل
        analysis = (
            f"📊 **تحليل السعر والمؤشرات:**\n\n"
            f"💵 **السعر الحالي:** `{last_price:.4f}`\n"
            f"📈 **RSI (14):** `{last_rsi:.2f}`\n"
            f"📉 **Stochastic (%K / %D):** `{last_k:.2f}` / `{last_d:.2f}`\n"
            f"📊 **SMA 20:** `{last_sma:.4f}`\n"
            f"📊 **EMA 200:** `{last_ema:.4f}`\n\n"
            f"🎯 **القرار:**\n{signal}"
        )
        return analysis

    except Exception as e:
        return f"⚠️ حدث خطأ أثناء التحليل: {str(e)}"
        
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

        # استخراج آخر القيم
        last_price = float(df['Close'].iloc[-1].item())
        last_rsi = float(df['RSI'].iloc[-1].item())
        last_k = float(df['%K'].iloc[-1].item())
        last_d = float(df['%D'].iloc[-1].item())
        last_sma = float(df['SMA20'].iloc[-1].item())
        last_ema = float(df['EMA200'].iloc[-1].item())

        # منطق تحديد التوصية بصورة مرنة
        if last_rsi < 45 and last_k < 45:
            signal = "🟢 **توصية: شراء (CALL)** \n*(اتجاه هابط قادم للارتداد)*"
        elif last_rsi > 55 and last_k > 55:
            signal = "🔴 **توصية: بيع (PUT)** \n*(اتجاه صاعد قادم للهبوط)*"
        elif last_rsi <= 50:
            signal = "🟢 **توصية: شراء خفيف**"
        else:
            signal = "🔴 **توصية: بيع خفيف**"

        # صياغة رسالة التحليل
        analysis = (
            f"📊 **تحليل السعر والمؤشرات:**\n\n"
            f"💵 **السعر الحالي:** `{last_price:.4f}`\n"
            f"📈 **RSI (14):** `{last_rsi:.2f}`\n"
            f"📉 **Stochastic (%K / %D):** `{last_k:.2f}` / `{last_d:.2f}`\n"
            f"📊 **SMA 20:** `{last_sma:.4f}`\n"
            f"📊 **EMA 200:** `{last_ema:.4f}`\n\n"
            f"🎯 **القرار:**\n{signal}"
        )
        return analysis

    except Exception as e:
        return f"⚠️ حدث خطأ أثناء التحليل: {str(e)}"
        
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

        # استخراج آخر القيم
        last_price = float(df['Close'].iloc[-1].item())
        last_rsi = float(df['RSI'].iloc[-1].item())
        last_k = float(df['%K'].iloc[-1].item())
        last_d = float(df['%D'].iloc[-1].item())
        last_sma = float(df['SMA20'].iloc[-1].item())
        last_ema = float(df['EMA200'].iloc[-1].item())

        # منطق تحديد التوصية التلقائية
        signal = "⚪ **انتظار (لا توجد إشارة قوية)**"
        
        if last_rsi < 35 and last_k < 25 and last_price > last_ema:
            signal = "🟢 **توصية: شراء (CALL)** \n*(تشبع بيعي + اتجاه صاعد)*"
        elif last_rsi > 65 and last_k > 75 and last_price < last_ema:
            signal = "🔴 **توصية: بيع (PUT)** \n*(تشبع شرائي + اتجاه هابط)*"
        elif last_rsi < 30:
            signal = "🟢 **توصية: شراء قريبة (مراقبة)**"
        elif last_rsi > 70:
            signal = "🔴 **توصية: بيع قريبة (مراقبة)**"

        # صياغة رسالة التحليل
        analysis = (
            f"📊 **تحليل السعر والمؤشرات:**\n\n"
            f"💵 **السعر الحالي:** `{last_price:.4f}`\n"
            f"📈 **RSI (14):** `{last_rsi:.2f}`\n"
            f"📉 **Stochastic (%K / %D):** `{last_k:.2f}` / `{last_d:.2f}`\n"
            f"📊 **SMA 20:** `{last_sma:.4f}`\n"
            f"📊 **EMA 200:** `{last_ema:.4f}`\n\n"
            f"🎯 **القرار:**\n{signal}"
        )
        return analysis

    except Exception as e:
        return f"⚠️ حدث خطأ أثناء التحليل: {str(e)}"
        
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
        bot.answer_callback_query(call.id, text="جاري جلب البيانات والتحليل...")
        asset = call.data
        
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
            response_text = analyze_asset(ticker)
            bot.send_message(call.message.chat.id, response_text, parse_mode="Markdown")
        except Exception as e:
            bot.send_message(call.message.chat.id, f"⚠️ حدث خطأ أثناء التحليل: {e}")
            
        
# تشغيل البوت
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling(timeout=60, long_polling_timeout=1)
    
