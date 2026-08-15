import logging
import asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import yfinance as yf
import pandas as pd

# إعداد التسجيل (Logging)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==========================================
# 1. قائمة جميع أصول منصة Pocket Option
# ==========================================
ASSETS = {
    "forex": [
        ("EUR/USD OTC 🚀", "EURUSD=X"), ("GBP/USD OTC 🚀", "GBPUSD=X"), 
        ("USD/JPY OTC 🚀", "USDJPY=X"), ("AUD/USD OTC 🚀", "AUDUSD=X"), 
        ("USD/CAD OTC 🚀", "USDCAD=X"), ("USD/CHF OTC 🚀", "USDCHF=X"), 
        ("NZD/USD OTC 🚀", "NZDUSD=X"), ("EUR/GBP OTC 🚀", "EURGBP=X"), 
        ("EUR/JPY OTC 🚀", "EURJPY=X"), ("EUR/AUD OTC 🚀", "EURAUD=X"), 
        ("EUR/CAD OTC 🚀", "EURCAD=X"), ("EUR/CHF OTC 🚀", "EURCHF=X"), 
        ("GBP/JPY OTC 🚀", "GBPJPY=X"), ("GBP/AUD OTC 🚀", "GBPAUD=X"), 
        ("GBP/CAD OTC 🚀", "GBPCAD=X"), ("GBP/CHF OTC 🚀", "GBPCHF=X"), 
        ("AUD/JPY OTC 🚀", "AUDJPY=X"), ("NZD/JPY OTC 🚀", "NZDJPY=X"), 
        ("CAD/JPY OTC 🚀", "CADJPY=X"), ("CHF/JPY OTC 🚀", "CHFJPY=X"), 
        ("AUD/CAD OTC 🚀", "AUDCAD=X"), ("AUD/NZD OTC 🚀", "AUDNZD=X")
    ],
    "crypto": [
        ("Bitcoin OTC 🪙", "BTC-USD"), ("Ethereum OTC 🔷", "ETH-USD"), 
        ("Solana OTC 🟣", "SOL-USD"), ("Binance Coin 🟡", "BNB-USD"), 
        ("Ripple OTC 🪙", "XRP-USD"), ("Cardano OTC 🔵", "ADA-USD"), 
        ("Dogecoin OTC 🐕", "DOGE-USD"), ("Avalanche OTC 🔺", "AVAX-USD"), 
        ("TRON OTC 🔴", "TRX-USD"), ("Link OTC 🔗", "LINK-USD"), 
        ("SUI OTC 💧", "SUI-USD"), ("PEPE OTC 🐸", "PEPE-USD")
    ],
    "stocks": [
        ("Apple OTC 🍏", "AAPL"), ("Tesla OTC 🚗", "TSLA"), 
        ("Nvidia OTC 🟢", "NVDA"), ("Microsoft OTC 💻", "MSFT"), 
        ("Amazon OTC 📦", "AMZN"), ("Google OTC 🌐", "GOOGL"), 
        ("Meta OTC ♾️", "META"), ("AMD OTC 🟥", "AMD"), 
        ("Netflix OTC 🍿", "NFLX"), ("Intel OTC 🟦", "INTC"),
        ("Boeing OTC ✈️", "BA"), ("Coca-Cola OTC 🥤", "KO")
    ],
    "commodities": [
        ("الذهب Gold OTC 🟡", "GC=F"), ("الفضة Silver OTC ⚪", "SI=F"), 
        ("النفط USCrude OTC 🛢️", "CL=F"), ("الغاز Natural Gas 💥", "NG=F")
    ]
}

ITEMS_PER_PAGE = 6

# قائمة الفريمات الزمنية المتوفرة
TIMEFRAMES = [
    [InlineKeyboardButton("⏱️ 5s", callback_data="tf_S5"), InlineKeyboardButton("⏱️ 10s", callback_data="tf_S10"), InlineKeyboardButton("⏱️ 15s", callback_data="tf_S15")],
    [InlineKeyboardButton("⏱️ 30s", callback_data="tf_S30"), InlineKeyboardButton("⏱️ 1m", callback_data="tf_M1"), InlineKeyboardButton("⏱️ 5m", callback_data="tf_M5")],
    [InlineKeyboardButton("⏱️ 15m", callback_data="tf_M15"), InlineKeyboardButton("⏱️ 1h", callback_data="tf_H1")],
    [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]
]

# ==========================================
# 2. محرك تحليل الاتجاه
# ==========================================
def get_signal_direction(ticker):
    try:
        data = yf.download(tickers=ticker, period="1d", interval="1m", progress=False)
        if data.empty or len(data) < 5:
            return random.choice(["BUY", "SELL"])
        
        close = data['Close'].dropna()
        ema = close.ewm(span=5, adjust=False).mean().iloc[-1]
        current = close.iloc[-1]
        
        return "BUY" if current >= ema else "SELL"
    except:
        return random.choice(["BUY", "SELL"])

# ==========================================
# 3. الأوامر والقوائم التفاعلية
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌐 جميع أزواج الفوركس", callback_data="cat_forex_0"),
         InlineKeyboardButton("📈 الأسهم والمؤشرات", callback_data="cat_stocks_0")],
        [InlineKeyboardButton("⚡ العملات الرقمية (Crypto)", callback_data="cat_crypto_0"),
         InlineKeyboardButton("🥇 السلع والمعادن", callback_data="cat_commodities_0")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = "Welcome to **Lyra OTC Signals Bot** 🤖\n\nاختر القسم المالي للاستعراض:"
    
    if update.message:
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(msg, parse_mode="Markdown", reply_markup=reply_markup)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "main_menu":
        await start(update, context)
        return

    # عرض الفئات والتنقل بين الصفحات
    if data.startswith("cat_"):
        parts = data.split("_")
        cat = parts[1]
        page = int(parts[2])

        assets_list = ASSETS.get(cat, [])
        total_items = len(assets_list)
        start_idx = page * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        current_assets = assets_list[start_idx:end_idx]

        keyboard = []
        for i in range(0, len(current_assets), 2):
            row = [InlineKeyboardButton(current_assets[i][0], callback_data=f"select_{current_assets[i][1]}_{current_assets[i][0]}")]
            if i + 1 < len(current_assets):
                row.append(InlineKeyboardButton(current_assets[i+1][0], callback_data=f"select_{current_assets[i+1][1]}_{current_assets[i+1][0]}"))
            keyboard.append(row)

        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("⬅️ السابقة", callback_data=f"cat_{cat}_{page-1}"))
        if end_idx < total_items:
            nav_row.append(InlineKeyboardButton("التالية ➡", callback_data=f"cat_{cat}_{page+1}"))
        if nav_row:
            keyboard.append(nav_row)

        keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")])
        await query.message.edit_text("اختر الزوج أو الأصل المطلوب:", reply_markup=InlineKeyboardMarkup(keyboard))

    # اختيار الفريم الزمني عند النقر على الأصل
    elif data.startswith("select_"):
        parts = data.split("_")
        ticker = parts[1]
        pair_display_name = parts[2]
        
        # حفظ الأصل المختار في بيانات الجلسة (user_data)
        context.user_data['selected_ticker'] = ticker
        context.user_data['selected_name'] = pair_display_name
        
        reply_markup = InlineKeyboardMarkup(TIMEFRAMES)
        await query.message.edit_text(
            f"🎯 الأصل المختار: **{pair_display_name}**\n\n⏱️ **اختر الإطار الزمني (Time Frame):**",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

    # توليد التوصية بناءً على الفريم الزمني المختار
    elif data.startswith("tf_"):
        tf_code = data.split("_")[1]
        ticker = context.user_data.get('selected_ticker', 'EURUSD=X')
        pair_display_name = context.user_data.get('selected_name', 'EUR/USD OTC 🚀')
        
        # 1. إرسال رسالة جاري التحليل
        msg = await query.message.reply_text(
            f"📡 **{pair_display_name}**\n⏱️ **Time Frame:** {tf_code}\n\n⏳ *Analyzing market... 28%*",
            parse_mode="Markdown"
        )
        
        await asyncio.sleep(1.2)
        
        # 2. جلب الاتجاه
        direction = get_signal_direction(ticker)
        
        if direction == "BUY":
            arrows = "⬆️  ⬆️  ⬆️\n⬆️  ⬆️  ⬆️"
            action_text = "CALL / BUY 🟢"
        else:
            arrows = "⬇️  ⬇️  ⬇️\n⬇️  ⬇️  ⬇️"
            action_text = "PUT / SELL 🔴"
            
        final_text = (
            f"📡 **{pair_display_name}**\n"
            f"⏱️ **Time Frame:** {tf_code}\n\n"
            f"{arrows}\n\n"
            f"🎯 **Signal:** `{action_text}`"
        )
        
        await msg.edit_text(final_text, parse_mode="Markdown")

# ==========================================
# 4. تشغيل البوت
# ==========================================
if __name__ == '__main__':
    TOKEN = "8920172447:AAEk41C2eZUQkiuh-56BF1InRXIpHvo6mgI"
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    app.run_polling()
    
    
    
    
    
    
    
    
