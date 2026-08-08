import os
import telebot
import yfinance as yf
import pandas as pd

# 1. تعريف البوت والتوكين في البداية
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)


# 2. قائمة الأصول
# قاموس شامل بجميع العملات والأصول المتاحة
ASSETS = {
    # 💵 أزواج العملات الرئيسية والتصاعدية (Forex)
    "EUR/USD 🇪🇺🇺🇸": "EURUSD=X",
    "GBP/USD 🇬🇧🇺🇸": "GBPUSD=X",
    "USD/JPY 🇺🇸🇯🇵": "JPY=X",
    "USD/CAD 🇺🇸🇨🇦": "CAD=X",
    "AUD/USD 🇦🇺🇺🇸": "AUDUSD=X",
    "USD/CHF 🇺🇸🇨🇭": "CHF=X",
    "NZD/USD 🇳🇿🇺🇸": "NZDUSD=X",
    "EUR/GBP 🇪🇺🇬🇧": "EURGBP=X",
    "EUR/JPY 🇪🇺🇯🇵": "EURJPY=X",
    "GBP/JPY 🇬🇧🇯🇵": "GBPJPY=X",
    "EUR/CAD 🇪🇺🇨🇦": "EURCAD=X",
    "EUR/AUD 🇪🇺🇦🇺": "EURAUD=X",
    "EUR/CHF 🇪🇺🇨🇭": "EURCHF=X",
    "GBP/CAD 🇬🇧🇨🇦": "GBPCAD=X",
    "GBP/AUD 🇬🇧🇦🇺": "GBPAUD=X",
    "GBP/CHF 🇬🇧🇨🇭": "GBPCHF=X",
    "AUD/CAD 🇦🇺🇨🇦": "AUDCAD=X",
    "AUD/JPY 🇦🇺🇯🇵": "AUDJPY=X",
    "AUD/NZD 🇦🇺🇳🇿": "AUDNZD=X",
    "NZD/JPY 🇳🇿🇯🇵": "NZDJPY=X",
    "CAD/JPY 🇨🇦🇯🇵": "CADJPY=X",
    "CHF/JPY 🇨🇭🇯🇵": "CHFJPY=X",

    # 🥇 المعادن والسلع
    "الذهب Gold 🥇": "GC=F",
    "الفضة Silver 🥈": "SI=F",
    "النفط Crude Oil 🛢️": "CL=F",

    # 🪙 العملات الرقمية (Crypto)
    "Bitcoin ₿": "BTC-USD",
    "Ethereum 💎": "ETH-USD",
    "Solana 🟣": "SOL-USD",
    "Binance Coin 🟡": "BNB-USD",
    "XRP 🚀": "XRP-USD",

    # 🏢 أسهم الشركات العالمية
    "Apple 🍏": "AAPL",
    "Microsoft 💻": "MSFT",
    "Google 🔍": "GOOGL",
    "Amazon 📦": "AMZN",
    "Tesla ⚡": "TSLA",
    "Meta 🌐": "META",
    "Nvidia 🟢": "NVDA",
    "Netflix 🎬": "NFLX",
    "McDonald's 🍔": "MCD",
    "Boeing ✈️": "BA",
    "Intel 🖥️": "INTC"
}

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
@bot.message_handler(func=lambda message: message.text in ASSETS)
def handle_asset_selection(message):
    symbol = ASSETS[message.text]
    bot.reply_to(message, f"⏳ جاري تحليل `{message.text}`...")
    result = analyze_asset(symbol)
    bot.send_message(message.chat.id, result, parse_mode="Markdown")
    
    

from telebot.types import ReplyKeyboardMarkup, KeyboardButton

@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [KeyboardButton(text) for text in ASSETS.keys()]
    markup.add(*buttons)
    
    bot.reply_to(
        message, 
        "📋 اختر الأصل لتليله واستخرج الإشارة:", 
        reply_markup=markup
    )
    
    
# 5. تشغيل البوت في النهاية فقط
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
    
    
    

            
            
            
            
            
    
                



            





    
    
    
    
    
    
    
    
    
    
    
