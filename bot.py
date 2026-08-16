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
TOKEN = "8920172447:AAFVnY7aZob1u9iNrZ7ULBagZ7kDbFCF_m8"

# ---------------------------------------------------------
# 1. قائمة الأصول المالية منصة بوكيت أوبشن (تمت إضافة EUR/USD)
# ---------------------------------------------------------
ASSETS = {
    "otc_high": {
        "🇪🇺🇺🇸 EUR/USD OTC": "EURUSD=X",  # تم التخصيص والإضافة هنا
        "🇦🇪 AED/CNY OTC": "AEDCNY=X",
        "🇳🇬 NGN/USD OTC": "NGNUSD=X",
        "🇪🇺 EUR/NZD OTC": "EURNZD=X",
        "🇷🇺 USD/RUB OTC": "USDRUB=X",
        "🇨🇦 AUD/CAD OTC": "AUDCAD=X",
        "🇨🇭 EUR/CHF OTC": "EURCHF=X",
        "🇪🇬 USD/EGP OTC": "USDEGP=X",
        "🇯🇵 AUD/JPY OTC": "AUDJPY=X",
        "🇺🇸 AUD/USD OTC": "AUDUSD=X"
    },
    "otc_forex": {
        "🇲🇦 MAD/USD OTC": "MADUSD=X",
        "🇯🇵 USD/JPY OTC": "USDJPY=X",
        "🇪🇺 EUR/JPY OTC": "EURJPY=X",
        "🇩ℤ USD/DZD OTC": "USDDZD=X",
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
# 2. خوارزمية التحليل الفني
# ---------------------------------------------------------
def analyze_market(ticker_symbol, timeframe='5s'):
    try:
        # جلب البيانات اللحظية بأسرع إطار (1m) لضمان الدقة
        data = yf.download(tickers=ticker_symbol, period='1d', interval='1m', progress=False)
        
        if data.empty or len(data) < 15:
            data = yf.download(tickers=ticker_symbol, period='5d', interval='5m', progress=False)
            
        if data.empty or len(data) < 5:
            return None

        close = data['Close'].squeeze()
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        # 1. حساب RSI (14)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        loss = loss.replace(0, 0.00001)
        rs = gain / loss
        rsi_series = 100 - (100 / (1 + rs))
        rsi = float(rsi_series.dropna().iloc[-1]) if not rsi_series.dropna().empty else 50.0

        # 2. EMA (9 و 21)
        ema9 = float(close.ewm(span=9, adjust=False).mean().iloc[-1])
        ema21 = float(close.ewm(span=21, adjust=False).mean().iloc[-1])

        # 3. Bollinger Bands (20, 2)
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        upper_band = float((sma20 + (std20 * 2)).dropna().iloc[-1]) if not sma20.dropna().empty else float(close.iloc[-1] * 1.01)
        lower_band = float((sma20 - (std20 * 2)).dropna().iloc[-1]) if not sma20.dropna().empty else float(close.iloc[-1] * 0.99)
        current_price = float(close.iloc[-1])

        # تحديد الإشارة
        signal = "WAIT"
        trend_desc = "اتجاه محايد / تذبذب ⚪"

        if current_price <= lower_band or rsi < 35 or (ema9 > ema21 and rsi < 55):
            signal = "BUY"
            trend_desc = "اتجاه صاعد (BUY) 🟢"
        elif current_price >= upper_band or rsi > 65 or (ema9 < ema21 and rsi > 45):
            signal = "SELL"
            trend_desc = "اتجاه هابط (SELL) 🔴"
        else:
            signal = "WAIT"
            trend_desc = "اتجاه محايد / تذبذب ⚪"

        return {
            "rsi": round(rsi, 2),
            "price": round(current_price, 5),
            "upper_band": round(upper_band, 5),
            "lower_band": round(lower_band, 5),
            "trend": trend_desc,
            "signal": signal
        }
    except Exception as e:
        logging.error(f"Error analyzing {ticker_symbol}: {e}")
        return None

# ---------------------------------------------------------
# 3. معالجة الواجهات والأزرار الجديدة للتايم فريم
# ---------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔥 عملات OTC (أعلى نسبة + EUR/USD)", callback_data='cat_otc_high')],
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
    await query.answer("جاري تحليل المؤشرات الفنية والسوق...")
    
    parts = query.data.split('_')
    symbol = parts[1]
    name = parts[2]
    timeframe = parts[3] if len(parts) > 3 else '5s'
    
    result = analyze_market(symbol, timeframe)
    
    if not result:
        await query.edit_message_text(
            "⚠️ تعذر جلب البيانات اللحظية، يرجى اختيار أصل آخر.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='main_menu')]])
        )
        return

    tf_labels = {
        "5s": "S5 (5 ثوانٍ)", 
        "10s": "S10 (10 ثوانٍ)", 
        "15s": "S15 (15 ثانية)", 
        "30s": "S30 (30 ثانية)", 
        "1m": "M1 (دقيقة واحدة)"
    }
    tf_display = tf_labels.get(timeframe, "S5 (5 ثوانٍ)")
    
    if result['signal'] == "BUY":
        rec_text = "🎯 التوصية: 🟢 CALL / BUY (شراء)"
    elif result['signal'] == "SELL":
        rec_text = "🎯 التوصية: 🔴 PUT / SELL (بيع)"
    else:
        rec_text = "🎯 التوصية: ⚪ WAIT (انتظار / عدم دخول)"

    text = (
        f"📊 تحليل منصة Pocket Option\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💱 الأصل المالي: {name}\n"
        f"⏱️ الإطار الزمني: {tf_display}\n"
        f"📈 حالة الاتجاه: {result['trend']}\n"
        f"💵 السعر الحالي: {result['price']}\n\n"
        f"🔍 قراءات المؤشرات:\n"
        f"🔹 RSI (14): {result['rsi']}\n"
        f"📊 Bollinger Upper: {result['upper_band']}\n"
        f"📊 Bollinger Lower: {result['lower_band']}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"{rec_text}"
    )

    # الأزرار الجديدة للأطر الزمنية السريعة (5 ثوانٍ، 10 ثوانٍ، 15 ثانية، 30 ثانية، دقيقة)
    keyboard = [
        [InlineKeyboardButton("🔄 تحديث التوصية", callback_data=f"select_{symbol}_{name}_{timeframe}")],
        [
            InlineKeyboardButton("⚡ 5 ثوانٍ", callback_data=f"select_{symbol}_{name}_5s"),
            InlineKeyboardButton("⚡ 10 ثوانٍ", callback_data=f"select_{symbol}_{name}_10s")
        ],
        [
            InlineKeyboardButton("⚡ 15 ثانية", callback_data=f"select_{symbol}_{name}_15s"),
            InlineKeyboardButton("⚡ 30 ثانية", callback_data=f"select_{symbol}_{name}_30s")
        ],
        [
            InlineKeyboardButton("⏱️ دقيقة واحدة (1m)", callback_data=f"select_{symbol}_{name}_1m")
        ],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='main_menu')]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ---------------------------------------------------------
# 4. تشغيل البوت
# ---------------------------------------------------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern='^main_menu$'))
    app.add_handler(CallbackQueryHandler(handle_category, pattern='^cat_'))
    app.add_handler(CallbackQueryHandler(send_signal, pattern='^select_'))

    print("🤖 Bot is running with quick timeframes & EUR/USD...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
    
    
        
    
    
    

    
    
    
    
    
    
    
    
    
    
    
    
