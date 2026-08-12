import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import yfinance as yf
import pandas as pd

# إعداد التسجيل (Logging)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==========================================
# 1. قائمة الأصول المالية (شاملة)
# ==========================================
ASSETS = {
    "forex": [
        ("EUR/USD 🇪🇺🇺🇸", "EURUSD=X"), ("GBP/USD 🇬🇧🇺🇸", "GBPUSD=X"), 
        ("USD/JPY 🇺🇸🇯🇵", "USDJPY=X"), ("AUD/USD 🇦🇺🇺🇸", "AUDUSD=X"), 
        ("USD/CAD 🇺🇸🇨🇦", "USDCAD=X"), ("USD/CHF 🇺🇸🇨🇭", "USDCHF=X"), 
        ("NZD/USD 🇳🇿🇺🇸", "NZDUSD=X"), ("EUR/GBP 🇪🇺🇬🇧", "EURGBP=X"), 
        ("EUR/JPY 🇪🇺🇯🇵", "EURJPY=X"), ("EUR/AUD 🇪🇺🇦🇺", "EURAUD=X"), 
        ("EUR/CAD 🇪🇺🇨🇦", "EURCAD=X"), ("EUR/CHF 🇪🇺🇨🇭", "EURCHF=X"), 
        ("EUR/NZD 🇪🇺🇳🇿", "EURNZD=X"), ("GBP/JPY 🇬🇧🇯🇵", "GBPJPY=X"), 
        ("GBP/AUD 🇬🇧🇦🇺", "GBPAUD=X"), ("GBP/CAD 🇬🇧🇨🇦", "GBPCAD=X"), 
        ("GBP/CHF 🇬🇧🇨🇭", "GBPCHF=X"), ("GBP/NZD 🇬🇧🇳🇿", "GBPNZD=X"), 
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
def analyze_market_advanced(ticker_symbol, interval="5m"):
    try:
        # جلب البيانات بحسب الفريم الزمني
        period = "1d" if interval in ["1m", "2m", "5m", "15m"] else "5d"
        data = yf.download(tickers=ticker_symbol, period=period, interval=interval, progress=False)

        if data.empty or len(data) < 30:
            return None, "لا توجد بيانات كافية للتحليل حالياً."

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        close = data['Close']
        high = data['High']
        low = data['Low']

        current_price = close.iloc[-1]

        # 1. RSI (14)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]

        # 2. MACD
        exp1 = close.ewm(span=12, adjust=False).mean()
        exp2 = close.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        current_macd = macd.iloc[-1] - signal.iloc[-1]

        # 3. Bollinger Bands (20)
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        upper_bb = (sma20 + (std20 * 2)).iloc[-1]
        mid_bb = sma20.iloc[-1]
        lower_bb = (sma20 - (std20 * 2)).iloc[-1]

        # 4. Stochastic Oscillator (%K, %D)
        low_14 = low.rolling(window=14).min()
        high_14 = high.rolling(window=14).max()
        k_percent = 100 * ((close - low_14) / (high_14 - low_14))
        current_k = k_percent.iloc[-1]

        # 5. Moving Averages (EMA 20 & EMA 50)
        ema20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
        
        # 6. Support & Resistance
        support = low.tail(20).min()
        resistance = high.tail(20).max()

        # توليد توصية احترافية مدمجة
        score = 0
        if current_rsi < 30: score += 2
        elif current_rsi > 70: score -= 2

        if current_k < 20: score += 1
        elif current_k > 80: score -= 1

        if current_price < lower_bb: score += 2
        elif current_price > upper_bb: score -= 2

        if current_price > ema20: score += 1
        else: score -= 1

        if score >= 3:
            signal_text = "🟢 **شراء قوي (STRONG BUY)**"
        elif score <= -3:
            signal_text = "🔴 **بيع قوي (STRONG SELL)**"
        elif score > 0:
            signal_text = "🟢 **شراء خفيف (WEAK BUY)**"
        elif score < 0:
            signal_text = "🔴 **بيع خفيف (WEAK SELL)**"
        else:
            signal_text = "⚪ **محايد / اتجاه عرضي (NEUTRAL)**"

        frame_labels = {"1m": "1 دقيقة", "5m": "5 دقائق", "15m": "15 دقيقة", "60m": "1 ساعة"}

        report = (
            f"📊 **تحليل محترف: {ticker_symbol}**\n"
            f"⏱️ **الإطار الزمني:** {frame_labels.get(interval, interval)}\n"
            f"💵 **السعر الحالي:** `{current_price:.4f}`\n\n"
            f"📈 **المؤشرات الفنية:**\n"
            f"• **RSI (14):** `{current_rsi:.2f}`\n"
            f"• **Stochastic %K:** `{current_k:.2f}`\n"
            f"• **MACD Hist:** `{current_macd:.4f}`\n"
            f"• **EMA (20):** `{ema20:.4f}`\n\n"
            f"📉 **بولينجر باندز:**\n"
            f"• العالي: `{upper_bb:.4f}` | الوسط: `{mid_bb:.4f}` | السفلي: `{lower_bb:.4f}`\n\n"
            f"🛡️ **الدعم والمقاومة اللحظية:**\n"
            f"• 🎯 **المقاومة (Resistance):** `{resistance:.4f}`\n"
            f"• 🛡️ **الدعم (Support):** `{support:.4f}`\n\n"
            f"🎯 **التوصية الاحترافية النهائية:**\n{signal_text}"
        )
        return report, None

    except Exception as e:
        return None, f"خطأ أثناء التحليل: {str(e)}"

# ==========================================
# 3. لوحة الأزرار والأوامر
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔱 جميع أزواج الفوركس", callback_data="cat_forex_0"),
         InlineKeyboardButton("📈 الأسهم والمؤشرات", callback_data="cat_stocks_0")],
        [InlineKeyboardButton("⚡ العملات الرقمية", callback_data="cat_crypto_0"),
         InlineKeyboardButton("🌍 السلع والمعادن", callback_data="cat_commodities_0")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = "مرحباً بك في **بوت التحليل الفني الاحترافي** 🚀\n\nاختر القسم المطلوب لاستعراض الأصول:"
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

    # استعراض الفئات والأجزاء
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
            row = [InlineKeyboardButton(current_assets[i][0], callback_data=f"selecttf_{current_assets[i][1]}")]
            if i + 1 < len(current_assets):
                row.append(InlineKeyboardButton(current_assets[i+1][0], callback_data=f"selecttf_{current_assets[i+1][1]}"))
            keyboard.append(row)

        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("⬅️ السابقة", callback_data=f"cat_{cat}_{page-1}"))
        if end_idx < total_items:
            nav_row.append(InlineKeyboardButton("التالية ➡", callback_data=f"cat_{cat}_{page+1}"))
        if nav_row:
            keyboard.append(nav_row)

        keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")])
        await query.message.edit_text("اختر الأصل المالي المطلوب:", reply_markup=InlineKeyboardMarkup(keyboard))

    # اختيار الفريم الزمني
    elif data.startswith("selecttf_"):
        symbol = data.split("_")[1]
        keyboard = [
            [InlineKeyboardButton("⏱️ 1 دقيقة", callback_data=f"analyze_{symbol}_1m"),
             InlineKeyboardButton("⏱️ 5 دقائق", callback_data=f"analyze_{symbol}_5m")],
            [InlineKeyboardButton("⏱️ 15 دقيقة", callback_data=f"analyze_{symbol}_15m"),
             InlineKeyboardButton("⏱️ 1 ساعة", callback_data=f"analyze_{symbol}_60m")],
            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]
        ]
        await query.message.edit_text(f"اختر الإطار الزمني لتحليل **{symbol}**:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    # تنفيذ التحليل
    elif data.startswith("analyze_"):
        parts = data.split("_")
        symbol = parts[1]
        interval = parts[2]

        await query.message.edit_text("⏳ جاري تحليل البيانات وإعداد التوصية الاحترافية...")
        report, error = analyze_market_advanced(symbol, interval)

        keyboard = [
            [InlineKeyboardButton("🔄 تحديث التحليل", callback_data=f"analyze_{symbol}_{interval}")],
            [InlineKeyboardButton("⏱️ تغيير الفريم الزمني", callback_data=f"selecttf_{symbol}")],
            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]
        ]
        
        if report:
            await query.message.edit_text(report, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.message.edit_text(f"❌ {error}", reply_markup=InlineKeyboardMarkup(keyboard))

# ==========================================
# 4. تشغيل البوت
# ==========================================
if __name__ == '__main__':
    # ضع التوكن الخاص بك هنا
    TOKEN = "8920172447:AAFPAfJyfLe9A7Avi6Ahidno0inMe0t9jyE"
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()
    
    
    
    
    
    
