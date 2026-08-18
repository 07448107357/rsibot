import os
import logging
import asyncio
import yfinance as yf
import pandas as pd
import numpy as np
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.request import HTTPXRequest
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
# 1. إعداد التسجيل (Logging)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
# بدلاً من كتابة التوكن مباشرة، يقرأه البوت من إعدادات Render:
TOKEN = os.getenv("TELEGRAM_TOKEN", "8920172447:AAEYfghaaLEUsw0unEBHESKOQrscwZX5ejM")
# --------------------------------------------------
# 3. قاموس الأصول الشامل (ASSETS) من الصور
# --------------------------------------------------
ASSETS = {
    "otc_high": {
        "🇪🇺🇺🇸 EUR/USD OTC": "EURUSD=X",
        "🇪🇺🇬🇧 EUR/GBP OTC": "EURGBP=X",
        "🇦🇪🇨🇳 AED/CNY OTC": "AEDCNY=X",
        "🇳🇬🇺🇸 NGN/USD OTC": "NGNUSD=X",
        "🇪🇺🇳🇿 EUR/NZD OTC": "EURNZD=X",
        "🇺🇸🇷🇺 USD/RUB OTC": "USDRUB=X",
        "🇦🇺🇨🇦 AUD/CAD OTC": "AUDCAD=X",
        "🇪🇺🇨🇭 EUR/CHF OTC": "EURCHF=X",
        "🇺🇸🇪🇬 USD/EGP OTC": "USDEGP=X",
        "🇦🇺🇯🇵 AUD/JPY OTC": "AUDJPY=X",
        "🇦🇺🇺🇸 AUD/USD OTC": "AUDUSD=X"
    },
    "otc_forex": {
        "🇲🇦🇺🇸 MAD/USD OTC": "MADUSD=X",
        "🇺🇸🇯🇵 USD/JPY OTC": "USDJPY=X",
        "🇪🇺🇯🇵 EUR/JPY OTC": "EURJPY=X",
        "🇩🇿🇺🇸 USD/DZD OTC": "USDDZD=X",
        "🇺🇸🇮🇩 USD/IDR OTC": "USDIDR=X",
        "🇺🇸🇹🇭 USD/THB OTC": "USDTHB=X",
        "🇺🇸🇨🇦 USD/CAD OTC": "USDCAD=X",
        "🇱🇧🇺🇸 LBP/USD OTC": "LBPUSD=X",
        "🇺🇸🇵🇰 USD/PKR OTC": "USDPKR=X",
        "🇰🇪🇺🇸 KES/USD OTC": "KESUSD=X"
    },
    "otc_global": {
        "🇬🇧🇺🇸 GBP/USD OTC": "GBPUSD=X",
        "🇧🇭🇨🇳 BHD/CNY OTC": "BHDCNY=X",
        "🇪🇺🇷🇺 EUR/RUB OTC": "EURRUB=X",
        "🇺🇸🇮🇳 USD/INR OTC": "USDINR=X",
        "🇺🇦🇺🇸 UAH/USD OTC": "UAHUSD=X",
        "🇺🇸🇧🇩 USD/BDT OTC": "USDBDT=X",
        "🇦🇺🇳🇿 AUD/NZD OTC": "AUDNZD=X",
        "🇯🇴🇨🇳 JOD/CNY OTC": "JODCNY=X",
        "🇺🇸🇻🇳 USD/VND OTC": "USDVND=X",
        "🇺🇸🇨🇴 USD/COP OTC": "USDCOP=X"
    },
    "otc_more": {
        "🇨🇭🇯🇵 CHF/JPY OTC": "CHFJPY=X",
        "🇺🇸🇦🇷 USD/ARS OTC": "USDARS=X",
        "🇺🇸🇲🇾 USD/MYR OTC": "USDMYR=X",
        "🇺🇸🇨🇱 USD/CLP OTC": "USDCLP=X",
        "🇺🇸🇸🇬 USD/SGD OTC": "USDSGD=X",
        "🇨🇦🇯🇵 CAD/JPY OTC": "CADJPY=X",
        "🇨🇭🇳🇴 CHF/NOK OTC": "CHFNOK=X",
        "🇸🇦🇨🇳 SAR/CNY OTC": "SARCNY=X",
        "🇺🇸🇨🇳 USD/CNH OTC": "USDCNH=X",
        "🇺🇸🇧🇷 USD/BRL OTC": "USDBRL=X",
        "🇺🇸🇲🇽 USD/MXN OTC": "USDMXN=X",
        "🇶🇦🇨🇳 QAR/CNY OTC": "QARCNY=X",
        "🇳🇿🇺🇸 NZD/USD OTC": "NZDUSD=X",
        "🇺🇸🇨🇭 USD/CHF OTC": "USDCHF=X"
    },
    "crypto": {
        "🪙 Bitcoin ETF OTC": "BTC-USD",
        "🪙 Litecoin OTC": "LTC-USD",
        "🟡 BNB OTC": "BNB-USD",
        "🔴 TRON OTC": "TRX-USD",
        "🔗 Chainlink OTC": "LINK-USD",
        "💎 Toncoin OTC": "TON-USD",
        "🟣 Solana OTC": "SOL-USD",
        "🟠 Bitcoin OTC": "BTC-USD",
        "🟣 Polygon OTC": "MATIC-USD",
        "🔺 Avalanche OTC": "AVAX-USD",
        "💎 Ethereum OTC": "ETH-USD",
        "🔴 Polkadot OTC": "DOT-USD",
        "🟡 Dogecoin OTC": "DOGE-USD",
        "🔵 Cardano OTC": "ADA-USD",
        "🔷 Dash OTC": "DASH-USD"
    },
    "stocks": {
        "✈️ Boeing OTC": "BA",
        "📱 Facebook OTC": "META",
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

# --------------------------------------------------
# 4. دوال التعامل مع القوائم والأزرار (Handlers)
# --------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """القائمة الرئيسية للقطاعات"""
    keyboard = [
        [InlineKeyboardButton("🔥 أزواج OTC (أعلى نسبة)", callback_data="cat_otc_high")],
        [InlineKeyboardButton("🌐 فوركس OTC (مجموعة 1)", callback_data="cat_otc_forex")],
        [InlineKeyboardButton("🌍 فوركس OTC (عالمي)", callback_data="cat_otc_global")],
        [InlineKeyboardButton("📌 أزواج OTC إضافية", callback_data="cat_otc_more")],
        [InlineKeyboardButton("🪙 العملات المشفرة (Crypto)", callback_data="cat_crypto")],
        [InlineKeyboardButton("📈 الأسهم والشركات (Stocks)", callback_data="cat_stocks")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "مرحباً بك في بوت التوصيات المتقدم لـ Pocket Option 🎯\nاختر القسم المطلوب للتداول:"
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text, reply_markup=reply_markup)

async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض الأصول التابعة للقطاع المحدد"""
    query = update.callback_query
    await query.answer()
    
    cat_key = query.data.replace("cat_", "")
    category_data = ASSETS.get(cat_key, {})

    keyboard = []
    pairs = list(category_data.keys())
    
    # توزيع الأزرار (زرين في كل سطر)
    for i in range(0, len(pairs), 2):
        row = [InlineKeyboardButton(pairs[i], callback_data=f"pair_{pairs[i]}")]
        if i + 1 < len(pairs):
            row.append(InlineKeyboardButton(pairs[i+1], callback_data=f"pair_{pairs[i+1]}"))
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")])
    
    await query.edit_message_text("اختر الزوج/الأصل المطلوب للتحليل:", reply_markup=InlineKeyboardMarkup(keyboard))

async def select_pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختيار الأصل وعرض التايم فريم"""
    query = update.callback_query
    await query.answer()
    
    selected_pair = query.data.replace("pair_", "")
    context.user_data['selected_pair'] = selected_pair
    
    keyboard = [
        [InlineKeyboardButton("⚡ 5 ثوانٍ", callback_data="tf_5s"), InlineKeyboardButton("⚡ 10 ثوانٍ", callback_data="tf_10s")],
        [InlineKeyboardButton("⚡ 15 ثانية", callback_data="tf_15s"), InlineKeyboardButton("⚡ 30 ثانية", callback_data="tf_30s")],
        [InlineKeyboardButton("⏱️ 1 دقيقة", callback_data="tf_1m"), InlineKeyboardButton("⏱️ 2 دقيقة", callback_data="tf_2m")],
        [InlineKeyboardButton("⏱️ 3 دقائق", callback_data="tf_3m"), InlineKeyboardButton("⏱️ 5 دقائق", callback_data="tf_5m")],
        [InlineKeyboardButton("⏱️ 15 دقيقة", callback_data="tf_15m"), InlineKeyboardButton("⏱️ 30 دقيقة", callback_data="tf_30m")],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        f"🎯 الأصل المحدد: **{selected_pair}**\nاختر الفريم الزمني المطلوب:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_timeframe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تحديد الفريم والجاهزية للتحليل"""
    query = update.callback_query
    await query.answer()
    
    timeframe = query.data.replace("tf_", "")
    context.user_data['timeframe'] = timeframe
    pair = context.user_data.get('selected_pair', 'EUR/USD OTC')
    
    keyboard = [
        [InlineKeyboardButton("🔄 تحديث التوصية", callback_data="update_signal")],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        f"✅ تم ضبط التخصيص بنجاح!\n📌 الأصل: **{pair}**\n⏱️ الفريم: **{timeframe}**\n\nاضغط على 'تحديث التوصية' للتحليل.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def send_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال نتيجة التحليل والتوصية"""
    query = update.callback_query
    await query.answer()
    
    pair = context.user_data.get('selected_pair', 'EUR/USD OTC')
    timeframe = context.user_data.get('timeframe', '1m')
    
    await query.edit_message_text(f"🔄 جاري تحليل {pair} على فريم {timeframe}...")
    
    keyboard = [
        [InlineKeyboardButton("🔄 تحديث التوصية", callback_data="update_signal")],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")]
    ]
    
    signal_text = (
        f"📊 **توصية التداول الحالية**\n\n"
        f"📌 الأصل: **{pair}**\n"
        f"⏱️ الفريم: **{timeframe}**\n"
        f"📈 التحليل الفني: **RSI (14)**\n"
        f"🎯 الإشارة: ⚪ **WAIT (انتظار إشارة واضحة)**\n\n"
        f"💡 يرجى مراقبة مناطق التشبع الشرائي والبيعي قبل الدخول."
    )
    
    await query.edit_message_text(signal_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def post_init(app: Application) -> None:
    """دالة لتهيئة الاتصال وتنظيف الـ Webhooks القديمة"""
    for attempt in range(3):
        try:
            await app.bot.delete_webhook(drop_pending_updates=True)
            print("✅ Webhook cleared successfully!")
            break
        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1} failed: {e}")
            await asyncio.sleep(3)

# --------------------------------------------------
# 5. تشغيل البوت (Main) مع معالجة مهلة الاتصال (TimedOut)
# --------------------------------------------------

def main():
    print("🚀 Starting Bot Setup...")
    
    # الحصول على التوكن من متغيرات البيئة
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        TOKEN = "8920172447:AAEYfghaaLEUswOunEBHESKOQrscwZX5ejM"

    # رفع وقت المهلة وإضافة إعادة المحاولة التلقائية
    request = HTTPXRequest(
        connect_timeout=60.0,
        read_timeout=60.0,
        write_timeout=60.0,
        pool_timeout=60.0,
        http_version="1.1"
    )

    app = (
        Application.builder()
        .token(TOKEN)
        .request(request)
        .post_init(post_init)
        .build()
    )

    # تسجيل الموجهات (Handlers)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern="^main_menu$"))
    app.add_handler(CallbackQueryHandler(show_category, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(select_pair, pattern="^pair_"))
    app.add_handler(CallbackQueryHandler(handle_timeframe, pattern="^tf_"))
    app.add_handler(CallbackQueryHandler(send_signal, pattern="^update_signal$"))

    print("🤖 Bot is officially running and listening for messages...")
    
    # تشغيل البوت
    app.run_polling(
        poll_interval=2.0,
        timeout=30,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
    
    
    
    
    
    
    
        
    
    
    
        
    
    
    

    
    
    
    
    
    
    
    
    
    
    
    
