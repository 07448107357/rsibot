import os
import logging
import asyncio
import yfinance as yf
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==========================================
# 1. موسوعة الأصول المالية الشاملة
# ==========================================
# ==========================================
# 1. موسوعة الأصول المالية الشاملة (جميع أزواج الفوركس)
# ==========================================
ASSETS = {
    "forex": [
        # الأزواج الرئيسية (Majors)
        ("EUR/USD 🇪🇺🇺🇸", "EURUSD=X"), ("GBP/USD 🇬🇧🇺🇸", "GBPUSD=X"), 
        ("USD/JPY 🇺🇸🇯🇵", "USDJPY=X"), ("AUD/USD 🇦🇺🇺🇸", "AUDUSD=X"), 
        ("USD/CAD 🇺🇸🇨🇦", "USDCAD=X"), ("USD/CHF 🇺🇸🇨🇭", "USDCHF=X"), 
        ("NZD/USD 🇳🇿🇺🇸", "NZDUSD=X"),

        # تقاطعات اليورو (Euro Crosses)
        ("EUR/GBP 🇪🇺🇬🇧", "EURGBP=X"), ("EUR/JPY 🇪🇺🇯🇵", "EURJPY=X"), 
        ("EUR/AUD 🇪🇺🇦🇺", "EURAUD=X"), ("EUR/CAD 🇪🇺🇨🇦", "EURCAD=X"), 
        ("EUR/CHF 🇪🇺🇨🇭", "EURCHF=X"), ("EUR/NZD 🇪🇺🇳🇿", "EURNZD=X"),

        # تقاطعات الباوند (GBP Crosses)
        ("GBP/JPY 🇬🇧🇯🇵", "GBPJPY=X"), ("GBP/AUD 🇬🇧🇦🇺", "GBPAUD=X"), 
        ("GBP/CAD 🇬🇧🇨🇦", "GBPCAD=X"), ("GBP/CHF 🇬🇧🇨🇭", "GBPCHF=X"), 
        ("GBP/NZD 🇬🇧🇳🇿", "GBPNZD=X"),

        # تقاطعات الين والعملات الأخرى (Other Crosses)
        ("AUD/JPY 🇦🇺🇯🇵", "AUDJPY=X"), ("NZD/JPY 🇳🇿🇯🇵", "NZDJPY=X"), 
        ("CAD/JPY 🇨🇦🇯🇵", "CADJPY=X"), ("CHF/JPY 🇨🇭🇯🇵", "CHFJPY=X"), 
        ("AUD/CAD 🇦🇺🇨🇦", "AUDCAD=X"), ("AUD/CHF 🇦🇺🇨🇭", "AUDCHF=X"), 
        ("AUD/NZD 🇦🇺🇳🇿", "AUDNZD=X"), ("NZD/CAD 🇳🇿🇨🇦", "NZDCAD=X"), 
        ("NZD/CHF 🇳🇿🇨🇭", "NZDCHF=X"), ("CAD/CHF 🇨🇦🇨🇭", "CADCHF=X")
    ],
    "crypto": [
        ("Bitcoin 🟠", "BTC-USD"), ("Ethereum 🔷", "ETH-USD"), ("Solana 🟣", "SOL-USD"),
        ("Binance Coin 🟡", "BNB-USD"), ("Ripple 🪙", "XRP-USD"), ("Cardano 🔵", "ADA-USD"),
        ("Dogecoin 🐕", "DOGE-USD"), ("Avalanche 🔺", "AVAX-USD"), ("TRON 🔴", "TRX-USD"),
        ("Link 🔗", "LINK-USD"), ("SUI 💧", "SUI-USD"), ("PEPE 🐸", "PEPE-USD")
    ],
    "commodities": [
        ("الذهب 🟡 (Gold)", "GC=F"), ("الفضة ⚪ (Silver)", "SI=F"), ("النفط الخام 🛢️ (WTI)", "CL=F"),
        ("نفط برنت 🛢️ (Brent)", "BZ=F"), ("الغاز الطبيعي 🔥 (Gas)", "NG=F"), ("النحاس 🟠 (Copper)", "HG=F"),
        ("البلاتين ⚪ (Platinum)", "PL=F"), ("البلاديوم 🔘 (Palladium)", "PA=F")
    ],
    "stocks": [
        ("Apple 🍏", "AAPL"), ("Tesla 🚗", "TSLA"), ("Nvidia 🟢", "NVDA"),
        ("Microsoft 💻", "MSFT"), ("Amazon 📦", "AMZN"), ("Google 🌐", "GOOGL"),
        ("Meta ♾️", "META"), ("AMD 🟥", "AMD"), ("Netflix 🍿", "NFLX"),
        ("مؤشر S&P 500 📈", "^GSPC"), ("مؤشر Nasdaq 📊", "^IXIC"), ("مؤشر Dow Jones 🏛️", "^DJI")
    ]
}


ITEMS_PER_PAGE = 6

# ==========================================
# 2. محرك التحليل الفني المتقدم
# ==========================================
def analyze_asset(symbol, interval="5m"):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="2d", interval=interval)
        
        if df.empty or len(df) < 25:
            return None

        close = df['Close']
        current_price = close.iloc[-1]

        # 1. RSI (14)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
        rs = gain / loss
        rsi_val = (100 - (100 / (1 + rs))).iloc[-1]

        # 2. MACD
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=9, adjust=False).mean()
        macd_val = macd.iloc[-1]
        sig_val = signal_line.iloc[-1]

        # 3. Bollinger Bands (20, 2)
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        upper_band = (sma20 + (std20 * 2)).iloc[-1]
        lower_band = (sma20 - (std20 * 2)).iloc[-1]
        middle_band = sma20.iloc[-1]

        # التوصية الفنية
        if current_price >= upper_band and rsi_val > 70 and macd_val < sig_val:
            signal = "🔴 بيع قوي (تشبع شرائي + اختراق الباند العلوي)"
        elif current_price <= lower_band and rsi_val < 30 and macd_val > sig_val:
            signal = "🟢 شراء قوي (تشبع بيعي + كسر الباند السفلي)"
        elif rsi_val > 60:
            signal = "🔴 ميل للهبوط / بيع خفيف"
        elif rsi_val < 40:
            signal = "🟢 ميل للصعود / شراء خفيف"
        else:
            signal = "⚪ محايد (استقرار السعر داخل النطاق)"

        return {
            "price": current_price,
            "rsi": rsi_val,
            "macd": macd_val,
            "bb_upper": upper_band,
            "bb_middle": middle_band,
            "bb_lower": lower_band,
            "signal": signal
        }
    except Exception as e:
        logging.error(f"Error analyzing {symbol}: {e}")
        return None

# ==========================================
# 3. واجهة التحكم والأزرار التفاعلية
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("جميع أزواج الفوركس 💱", callback_data="cat_forex_0"),
         InlineKeyboardButton("الأسهم والمؤشرات 📈", callback_data="cat_stocks_0")],
        [InlineKeyboardButton("السلع والمعادن 🌍", callback_data="cat_commodities_0"),
         InlineKeyboardButton("العملات الرقمية ⚡", callback_data="cat_crypto_0")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = "مرحباً بك في بوت التحليل الفني الشامل للبورصة العالمية 👋\n\nاختر القسم للاستعراض وتحليل الأسعار لحظياً:"
    
    if update.message:
        await update.message.reply_text(msg, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(msg, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "main_menu":
        await start(update, context)
        return

    # عرض القوائم المقسمة لتناسب الشاشة
    if data.startswith("cat_"):
        parts = data.split("_")
        category = parts[1]
        page = int(parts[2])
        
        assets = ASSETS.get(category, [])
        start_idx = page * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        current_assets = assets[start_idx:end_idx]

        keyboard = []
        for i in range(0, len(current_assets), 2):
            row = [InlineKeyboardButton(current_assets[i][0], callback_data=f"asset_{current_assets[i][1]}")]
            if i + 1 < len(current_assets):
                row.append(InlineKeyboardButton(current_assets[i+1][0], callback_data=f"asset_{current_assets[i+1][1]}"))
            keyboard.append(row)

        # أزرار الانتقال بين الصفحات
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("⬅️ السابقة", callback_data=f"cat_{category}_{page-1}"))
        if end_idx < len(assets):
            nav_row.append(InlineKeyboardButton("التالية ➡️", callback_data=f"cat_{category}_{page+1}"))
        
        if nav_row:
            keyboard.append(nav_row)

        keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")])
        await query.message.edit_text("اختر الأصل المالي المطلوب للتحليل اللحظي:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    # طلب تحليل الأصل المالي
    if data.startswith("asset_"):
        symbol = data.split("asset_")[1]
        await query.message.edit_text(f"⏳ جاري تحليل `{symbol}` ومسح المؤشرات...", parse_mode="Markdown")
        
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, analyze_asset, symbol, "5m")
        
        keyboard = [[InlineKeyboardButton("🔙 الرجوع للقائمة", callback_data="main_menu")]]
        
        if res:
            msg = (f"📊 **تحليل:** `{symbol}`\n"
                   f"⏱️ **الإطار الزمني:** 5 دقائق\n"
                   f"ــــــــــــــــــــــــــــــــــــــــ\n"
                   f"💵 **السعر الحالي:** `{res['price']:.4f}`\n"
                   f"📈 **RSI (14):** `{res['rsi']:.2f}`\n"
                   f"📉 **MACD:** `{res['macd']:.4f}`\n"
                   f"ــــــــــــــــــــــــــــــــــــــــ\n"
                   f"🟡 **بولينجر العالي:** `{res['bb_upper']:.4f}`\n"
                   f"⚪ **بولينجر الوسط:** `{res['bb_middle']:.4f}`\n"
                   f"🔵 **بولينجر السفلي:** `{res['bb_lower']:.4f}`\n"
                   f"ــــــــــــــــــــــــــــــــــــــــ\n"
                   f"🎯 **التوصية اللحظية:**\n {res['signal']}")
        else:
            msg = "❌ فشل جلب البيانات. قد يكون السوق مغلقاً حالياً أو الرمز بحاجة لتحديث."
            
        await query.message.edit_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# ==========================================
# 4. تشغيل التطبيق
# ==========================================
if __name__ == '__main__':
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("Full Trading Bot is running...")
    app.run_polling()
    
    
    
    
    
