import os
import logging
import yfinance as yf
import pandas as pd
import numpy as np
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# إعداد التسجيل (Logging)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 🔑 ضع التوكن الخاص بك هنا
TOKEN = "8920172447:AAF0wf_-TG5G7QhV3WRJr8uzNyNS9vSHlFc"

# ---------------------------------------------------------
# 1. قائمة الأصول المالية المستخرجة من منصة بوكيت أوبشن
# ---------------------------------------------------------
ASSETS = {
    "otc_high": {
        "🇦🇪 AED/CNY OTC": "AEDCNY=X",
        "🇳🇬 NGN/USD OTC": "NGNUSD=X",
        "🇪🇺 EUR/NZD OTC": "EURNZD=X",
        "🇷🇺 USD/RUB OTC": "USDRUB=X",
        "🇨🇦 AUD/CAD OTC": "AUDCAD=X",
        "🇨🇭 EUR/CHF OTC": "EURCHF=X",
        "🇪🇬 USD/EGP OTC": "USDEGP=X",
        "🇯🇵 AUD/JPY OTC": "AUDJPY=X",
        "🇺🇸 AUD/USD OTC": "AUDUSD=X",
        "🇭🇺 EUR/HUF OTC": "EURHUF=X"
    },
    "otc_forex": {
        "🇲🇦 MAD/USD OTC": "MADUSD=X",
        "🇯🇵 USD/JPY OTC": "USDJPY=X",
        "🇪🇺 EUR/JPY OTC": "EURJPY=X",
        "🇩🇿 USD/DZD OTC": "USDDZD=X",
        "🇮🇩 USD/IDR OTC": "USDIDR=X",
        "🇹🇭 USD/THB OTC": "USDTHB=X",
        "🇨🇦 USD/CAD OTC": "USDCAD=X",
        "🇱🇧 LBP/USD OTC": "LBPUSD=X",
        "🇵🇰 USD/PKR OTC": "USDPKR=X",
        "🇰🇪 KES/USD OTC": "KESUSD=X"
    },
    "otc_global": {
        "🇬🇧 GBP/USD OTC": "GBPUSD=X",
        "🇧🇭 BHD/CNY OTC": "BHDCNY=X",
        "🇪🇺 EUR/RUB OTC": "EURRUB=X",
        "🇮🇳 USD/INR OTC": "USDINR=X",
        "🇺🇦 UAH/USD OTC": "UAHUSD=X",
        "🇧🇩 USD/BDT OTC": "USDBDT=X",
        "🇦🇺 AUD/NZD OTC": "AUDNZD=X",
        "🇯🇴 JOD/CNY OTC": "JODCNY=X",
        "🇻🇳 USD/VND OTC": "USDVND=X",
        "🇨🇴 USD/COP OTC": "USDCOP=X"
    },
    "otc_more": {
        "🇯🇵 CHF/JPY OTC": "CHFJPY=X",
        "🇦🇷 USD/ARS OTC": "USDARS=X",
        "🇲🇾 USD/MYR OTC": "USDMYR=X",
        "🇨🇱 USD/CLP OTC": "USDCLP=X",
        "🇸🇬 USD/SGD OTC": "USDSGD=X",
        "🇯🇵 CAD/JPY OTC": "CADJPY=X",
        "🇳🇴 CHF/NOK OTC": "CHFNOK=X",
        "🇸🇦 SAR/CNY OTC": "SARCNY=X",
        "🇨🇳 USD/CNH OTC": "USDCNH=X",
        "🇧🇷 USD/BRL OTC": "USDBRL=X",
        "🇲🇽 USD/MXN OTC": "USDMXN=X",
        "🇶🇦 QAR/CNY OTC": "QARCNY=X",
        "🇳🇿 NZD/USD OTC": "NZDUSD=X",
        "🇨🇭 USD/CHF OTC": "USDCHF=X"
    },
    "stocks": {
        "✈️ Boeing OTC": "BA",
        "📘 Facebook OTC": "META",
        "⛽ ExxonMobil OTC": "XOM",
        "💻 AMD OTC": "AMD",
        "📦 Amazon OTC": "AMZN",
        "🛒 Alibaba OTC": "BABA",
        "⛏️ Marathon Digital OTC": "MARA",
        "📊 VIX OTC": "^VIX",
        "💳 VISA OTC": "V",
        "🎬 Netflix OTC": "NFLX",
        "🍔 McDonald's OTC": "MCD",
        "📦 FedEx OTC": "FDX",
        "💻 Microsoft OTC": "MSFT",
        "💊 Pfizer OTC": "PFE",
        "🍏 Apple OTC": "AAPL",
        "🪙 Coinbase OTC": "COIN",
        "🚗 Tesla OTC": "TSLA",
        "🌐 Cisco OTC": "CSCO",
        "🏦 Citigroup OTC": "C",
        "👁️ Palantir OTC": "PLTR",
        "🟦 Intel OTC": "INTC"
    }
}

# ---------------------------------------------------------
# 2. خوارزمية التحليل الفني (RSI + EMA + Bollinger Bands)
# ---------------------------------------------------------
def analyze_market(ticker_symbol, timeframe='5m'):
    try:
        # تحويل صيغ التايم فريم لـ yfinance
        interval_map = {'5m': '5m', '15m': '15m', '30m': '30m', '1h': '60m'}
        yf_interval = interval_map.get(timeframe, '5m')
        
        # جلب البيانات
        data = yf.download(tickers=ticker_symbol, period='5d', interval=yf_interval, progress=False)
        
        if data.empty or len(data) < 20:
            return "عذراً، تعذر جلب البيانات الحالية لهذا الأصل."

        close = data['Close'].squeeze()

        # 1. RSI (14)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = float((100 - (100 / (1 + rs))).iloc[-1])

        # 2. EMA (9, 21)
        ema9 = float(close.ewm(span=9, adjust=False).mean().iloc[-1])
        ema21 = float(close.ewm(span=21, adjust=False).mean().iloc[-1])

        # 3. Bollinger Bands (20, 2)
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        upper_band = float((sma20 + (std20 * 2)).iloc[-1])
        lower_band = float((sma20 - (std20 * 2)).iloc[-1])
        current_price = float(close.iloc[-1])

        # منطق تحديد الاتجاه والتوصية
        signal = "WAIT"
        trend_desc = "اتجاه محايد / تذبذب ⚪"

        if current_price <= lower_band or (ema9 > ema21 and rsi < 60):
            signal = "BUY"
            trend_desc = "اتجاه صاعد (BUY) 🟢"
        elif current_price >= upper_band or (ema9 < ema21 and rsi > 40):
            signal = "SELL"
            trend_desc = "اتجاه هابط (SELL) 🔴"

        return {
            "rsi": round(rsi, 2),
            "price": round(current_price, 5),
            "upper_band": round(upper_band, 5),
            "lower_band": round(lower_band, 5),
            "trend": trend_desc,
            "signal": signal
        }
    except Exception as e:
        logging.error(f"Error in analysis: {e}")
        return None

# ---------------------------------------------------------
# 3. معالجة واجهة أزرار تلغرام (UI Handlers)
# ---------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔥 عملات OTC (نسب عالية 1)", callback_data='cat_otc_high')],
        [InlineKeyboardButton("🌐 عملات OTC (مجموعة 2)", callback_data='cat_otc_forex')],
        [InlineKeyboardButton("💱 عملات OTC (مجموعة 3)", callback_data='cat_otc_global')],
        [InlineKeyboardButton("📌 عملات OTC (باقي الأزواج)", callback_data='cat_otc_more')],
        [InlineKeyboardButton("📈 أسهم بوكيت أوبشن (Stocks)", callback_data='cat_stocks')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = "مرحباً بك في بوت التوصيات المتقدم لـ Pocket Option 🎯\nاختر القسم المطلوب للتداول:"
    
    if update.message:
        await update.message.reply_text(msg, reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(msg, reply_markup=reply_markup)

async def handle_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.replace('cat_', '')
    
    keyboard = []
    category_assets = ASSETS.get(category, {})
    
    row = []
    for name, symbol in category_assets.items():
        # اختصار اسم العرض للأزرار
        clean_name = name.split()[0] + " " + name.split()[1] if len(name.split()) > 1 else name
        row.append(InlineKeyboardButton(name, callback_data=f"select_{symbol}_{clean_name}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='main_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("اختر الزوج أو الأصل المالي للحصول على التوصية الحية:", reply_markup=reply_markup)

async def send_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("جاري تحليل المؤشرات الفنية (RSI, Bollinger Bands)...")
    
    parts = query.data.split('_')
    symbol = parts[1]
    name = parts[2]
    timeframe = parts[3] if len(parts) > 3 else '5m'
    
    result = analyze_market(symbol, timeframe)
    
    if not result or isinstance(result, str):
        await query.edit_message_text(
            "⚠️ تعذر جلب البيانات لهذا الأصل حالياً، يرجى اختيار أصل آخر.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='main_menu')]])
        )
        return

    tf_labels = {"5m": "M5 (5 دقائق)", "15m": "M15 (15 دقيقة)", "30m": "M30 (30 دقيقة)", "1h": "H1 (ساعة)"}
    tf_display = tf_labels.get(timeframe, "M5")
    
    if result['signal'] == "BUY":
        rec_text = "🎯 <b>التوصية:</b> 🟢 CALL / BUY (شراء)"
    elif result['signal'] == "SELL":
        rec_text = "🎯 <b>التوصية:</b> 🔴 PUT / SELL (بيع)"
    else:
        rec_text = "🎯 <b>التوصية:</b> ⚪ WAIT (انتظار)"

    # تنسيق الرسالة باستخدام HTML لتفادي مشكلة اتجاه النص والرموز الغريبة
    text = (
        f"📊 <b>تحليل منصة Pocket Option</b>\n"
        f"───────────────────\n"
        f"💱 <b>الأصل المالي:</b> {name}\n"
        f"⏱️ <b>الإطار الزمني:</b> {tf_display}\n"
        f"📈 <b>حالة الاتجاه:</b> {result['trend']}\n"
        f"💵 <b>السعر الحالي:</b> <code>{result['price']}</code>\n\n"
        f"🔍 <b>قراءات المؤشرات:</b>\n"
        f"🔹 <b>RSI (14):</b> <code>{result['rsi']}</code>\n"
        f"📊 <b>Bollinger Upper:</b> <code>{result['upper_band']}</code>\n"
        f"📊 <b>Bollinger Lower:</b> <code>{result['lower_band']}</code>\n"
        f"───────────────────\n"
        f"{rec_text}"
    )

    keyboard = [
        [InlineKeyboardButton("🔄 تحديث التوصية", callback_data=f"select_{symbol}_{name}_{timeframe}")],
        [
            InlineKeyboardButton("⏱️ 5 دقائق", callback_data=f"select_{symbol}_{name}_5m"),
            InlineKeyboardButton("⏱️ 15 دقيقة", callback_data=f"select_{symbol}_{name}_15m")
        ],
        [
            InlineKeyboardButton("⏱️ 30 دقيقة", callback_data=f"select_{symbol}_{name}_30m"),
            InlineKeyboardButton("⏱️ ساعة كاملة", callback_data=f"select_{symbol}_{name}_1h")
        ],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='main_menu')]
    ]
    
    # استخدام parse_mode='HTML' هنا يحل مشكلة التنسيق تماماً
    await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    

    # أزرار التايم فريم المطلوبة (من 5 دقائق إلى ساعة) + زر التحديث
    keyboard = [
        [InlineKeyboardButton("🔄 تحديث التوصية", callback_data=f"select_{symbol}_{name}_{timeframe}")],
        [
            InlineKeyboardButton("⏱️ 5 دقائق", callback_data=f"select_{symbol}_{name}_5m"),
            InlineKeyboardButton("⏱️ 15 دقيقة", callback_data=f"select_{symbol}_{name}_15m")
        ],
        [
            InlineKeyboardButton("⏱️ 30 دقيقة", callback_data=f"select_{symbol}_{name}_30m"),
            InlineKeyboardButton("⏱️ ساعة كاملة", callback_data=f"select_{symbol}_{name}_1h")
        ],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='main_menu')]
    ]
    
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

# ---------------------------------------------------------
# 4. تشغيل البوت
# ---------------------------------------------------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern='^main_menu$'))
    app.add_handler(CallbackQueryHandler(handle_category, pattern='^cat_'))
    app.add_handler(CallbackQueryHandler(send_signal, pattern='^select_'))

    print("🤖 Bot is running successfully with Pocket Option assets...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
        
    
    
    

    
    
    
    
    
    
    
    
    
    
    
    
