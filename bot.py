import os
import logging
import yfinance as yf
import pandas as pd
import numpy as np
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.request import HTTPXRequest
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
# إعداد التسجيل (Logging)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
# 🔑 ضع/ضعي التوكن الخاص بك هنا بين علامات التنصيص
TOKEN = "8920172447:AAGJXxHcTpK-6q0AovygTNnjaL3ABrEI_P0"
# ---------------------------------------------------------
# 1. قائمة الأصول المالية (تم إضافة EUR/GBP OTC)
# ---------------------------------------------------------
ASSETS = {
    "otc_high": {
        "🇪🇺🇺🇸 EUR/USD OTC": "EURUSD=X",
        "🇪🇺🇬🇧 EUR/GBP OTC": "EURGBP=X",
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
# 2. خوارزمية التحليل الفني المحدثة (تتبع لون الشمعة والاتجاه)
# ---------------------------------------------------------
def analyze_market(df):
    try:
        close = df['close']
        
        # 1. حساب RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = float((100 - (100 / (1 + rs))).dropna().iloc[-1])

        # 2. حساب Bollinger Bands (20, 2)
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        upper_band = float((sma20 + (std20 * 2)).dropna().iloc[-1])
        lower_band = float((sma20 - (std20 * 2)).dropna().iloc[-1])

        # 3. السعر الحالي
        last_close = float(close.iloc[-1])

        # 4. شروط التداول المرنة
        if rsi <= 40 and last_close <= lower_band * 1.0005:
            signal = "BUY 🟢"
            trend_desc = "شراء (تشبع بيعي واقتراب من دعم البولنجر)"
        elif rsi >= 60 and last_close >= upper_band * 0.9995:
            signal = "SELL 🔴"
            trend_desc = "بيع (تشبع شرائي واقتراب من مقاومة البولنجر)"
        else:
            signal = "WAIT ⚪"
            trend_desc = "انتظار (السوق في منطقة محايدة)"

        return {
            "rsi": round(rsi, 2),
            "price": round(last_close, 5),
            "upper_band": round(upper_band, 5),
            "lower_band": round(lower_band, 5),
            "trend": trend_desc,
            "signal": signal
        }

    except Exception as e:
        print(f"Error in analyze_market: {e}")
        return None
        
        

# ---------------------------------------------------------
# 3. معالجة الواجهات
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
        # ربط الأزرار بالدوال الصحيحة
    app.add_handler(CallbackQueryHandler(handle_timeframe, pattern="^(1m|2m|3m|5m|15m|30m|1h|5s|10s|15s|30s)$"))
    app.add_handler(CallbackQueryHandler(send_signal, pattern="^update_signal$"))
    app.add_handler(CallbackQueryHandler(start, pattern="^main_menu$"))
    
    parts = query.data.split('_')
    symbol = parts[1]
    name = parts[2]
    timeframe = parts[3] if len(parts) > 3 else '5m'
    
    result = analyze_market(symbol, timeframe)
    
    if not result:
        await query.edit_message_text(
            "⚠️ تعذر جلب البيانات اللحظية، يرجى اختيار أصل آخر.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='main_menu')]])
        )
        return

    tf_labels = {
        "5s": "⚡ 5 ثوانٍ", "10s": "⚡ 10 ثوانٍ", "15s": "⚡ 15 ثانية", "30s": "⚡ 30 ثانية",
        "1m": "⏱️ دقيقة (1m)", "2m": "⏱️ دقيقتين (2m)", "3m": "⏱️ 3 دقائق (3m)",
        "5m": "⏱️ 5 دقائق (5m)", "15m": "⏱️ 15 دقيقة (15m)", "30m": "⏱️ 30 دقيقة (30m)", "1h": "⏱️ ساعة كاملة (1h)"
    }
    tf_display = tf_labels.get(timeframe, "⏱️ 5 دقائق (5m)")
    
    if result['signal'] == "BUY":
        rec_text = "🎯 التوصية: 🟢 CALL / BUY (شراء مع الارتداد)"
    elif result['signal'] == "SELL":
        rec_text = "🎯 التوصية: 🔴 PUT / SELL (بيع مع الارتداد)"
    else:
        rec_text = f"🎯 التوصية: ⚪ WAIT ({result['trend']})"

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
            InlineKeyboardButton("⏱️ 1 دقيقة", callback_data=f"select_{symbol}_{name}_1m"),
            InlineKeyboardButton("⏱️ 2 دقيقة", callback_data=f"select_{symbol}_{name}_2m"),
            InlineKeyboardButton("⏱️ 3 دقائق", callback_data=f"select_{symbol}_{name}_3m")
        ],
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
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# --------------------------------------------------
# 4. تشغيل البوت
# --------------------------------------------------
async def post_init(app: Application) -> None:
    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook cleared successfully!")
    except Exception as e:
        print(f"⚠️ Webhook clear failed: {e}")

def main():
    print("🚀 Starting Bot Setup...")
    
    # رفع مهلة الانتظار
    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0
    )

    app = (
        Application.builder()
        .token(TOKEN)
        .request(request)
        .post_init(post_init)
        .build()
    )

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_timeframe, pattern="^(1m|2m|3m|5m|15m|30m|1h|5s|10s|15s|30s)$"))
    app.add_handler(CallbackQueryHandler(send_signal, pattern="^update_signal$"))
    app.add_handler(CallbackQueryHandler(start, pattern="^main_menu$"))

    print("🤖 Bot is officially running and listening for messages...")
    app.run_polling(poll_interval=1.0, timeout=20)

if __name__ == "__main__":
    main()
    
    
    
    
    
    
        
    
    
    
        
    
    
    

    
    
    
    
    
    
    
    
    
    
    
    
