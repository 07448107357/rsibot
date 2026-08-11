import os
import yfinance as yf
import pandas as pd
import numpy as np
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ==================== موسوعة الأصول المزودة بالألوان والرموز ====================
FOREX_PAIRS = {
    "🟢 EUR/USD": "EURUSD=X", "🔵 GBP/USD": "GBPUSD=X", "🔴 USD/JPY": "JPY=X", 
    "🇨🇦 USD/CAD": "CAD=X", "🇦🇺 AUD/USD": "AUDUSD=X", "🇨🇭 USD/CHF": "CHF=X", 
    "🇳🇿 NZD/USD": "NZDUSD=X", "🇪🇺 EUR/GBP": "EURGBP=X", "🇯🇵 EUR/JPY": "EURJPY=X", 
    "🇬🇧 GBP/JPY": "GBPJPY=X", "🇨🇦 EUR/CAD": "EURCAD=X", "🇨🇦 GBP/CAD": "GBPCAD=X", 
    "🇦🇺 AUD/JPY": "AUDJPY=X", "🇯🇵 CAD/JPY": "CADJPY=X", "🇨🇭 CHF/JPY": "CHFJPY=X", 
    "🇦🇺 EUR/AUD": "EURAUD=X", "🇳🇿 EUR/NZD": "EURNZD=X", "🇦🇺 GBP/AUD": "GBPAUD=X",
    "🇳🇿 GBP/NZD": "GBPNZD=X", "🇨🇭 AUD/CHF": "AUDCHF=X", "🇨🇦 AUD/CAD": "AUDCAD=X",
    "🇳🇿 AUD/NZD": "AUDNZD=X", "🇨🇭 CAD/CHF": "CADCHF=X", "🇸🇬 USD/SGD": "USDSGD=X"
}

STOCKS = {
    "🍏 Apple": "AAPL", "🚗 Tesla": "TSLA", "🟩 NVIDIA": "NVDA", "📦 Amazon": "AMZN",
    "🪟 Microsoft": "MSFT", "🎬 Netflix": "NFLX", "🔍 Google": "GOOGL", "♾️ Meta": "META",
    "🔴 AMD": "AMD", "🔵 Intel": "INTC"
}

COMMODITIES = {
    "🟡 الذهب (Gold)": "GC=F", 
    "⚪ الفضة (Silver)": "SI=F", 
    "🛢️ النفط الخام (Oil)": "CL=F",
    "🔥 الغاز الطبيعي (Gas)": "NG=F",
    "🥉 النحاس (Copper)": "HG=F"
}

CRYPTO = {
    "🟠 Bitcoin": "BTC-USD", "🟣 Ethereum": "ETH-USD", "🟢 Solana": "SOL-USD",
    "🔵 XRP": "XRP-USD", "🟡 Binance Coin": "BNB-USD", "🔴 Cardano": "ADA-USD"
}

SYMBOL_MAP = {**FOREX_PAIRS, **STOCKS, **COMMODITIES, **CRYPTO}

TIMEFRAME_MAP = {
    "1m": {"interval": "1m", "period": "1d", "label": "دقيقة واحدة (1m)"},
    "5m": {"interval": "5m", "period": "5d", "label": "5 دقائق (5m)"},
    "15m": {"interval": "15m", "period": "5d", "label": "15 دقيقة (15m)"}
}

SUBSCRIBED_USERS = set()

# ==================== المؤشرات الفنية ====================
def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_bollinger_bands(series: pd.Series, period: int = 20, std_dev: int = 2):
    sma = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    return sma + (std * std_dev), sma - (std * std_dev), sma

def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3):
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    d = k.rolling(window=d_period).mean()
    return k, d

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    true_range = np.max(pd.concat([high_low, high_close, low_close], axis=1), axis=1)
    return true_range.rolling(period).mean()

# ==================== تحليل فني محسن بمؤشر بولينجر ====================
def analyze_asset(symbol_key: str, tf_key: str = "5m") -> dict:
    ticker = SYMBOL_MAP.get(symbol_key, symbol_key)
    tf_info = TIMEFRAME_MAP.get(tf_key, TIMEFRAME_MAP["5m"])
    
    try:
        df = yf.download(tickers=ticker, period=tf_info["period"], interval=tf_info["interval"], progress=False)
        if df.empty or len(df) < 20:
            return {"error": f"البيانات غير متوفرة حالياً لـ {symbol_key}."}

        if isinstance(df.columns, pd.MultiIndex):
            close = df['Close'][ticker].dropna()
            high = df['High'][ticker].dropna()
            low = df['Low'][ticker].dropna()
        else:
            close = df['Close'].dropna()
            high = df['High'].dropna()
            low = df['Low'].dropna()

        rsi = calculate_rsi(close, 14)
        upper_band, lower_band, sma20 = calculate_bollinger_bands(close, 20, 2)
        macd, macd_sig, macd_hist = calculate_macd(close)
        ema50 = close.ewm(span=50, adjust=False).mean()
        atr = calculate_atr(pd.DataFrame({'High': high, 'Low': low, 'Close': close}), 14)

        is_forex = "=X" in ticker
        decimals = 5 if is_forex else 2

        last_price = round(float(close.iloc[-1]), decimals)
        last_rsi = round(float(rsi.fillna(50).iloc[-1]), 2)
        last_upper = round(float(upper_band.fillna(last_price).iloc[-1]), decimals)
        last_lower = round(float(lower_band.fillna(last_price).iloc[-1]), decimals)
        last_ema = round(float(ema50.iloc[-1]), decimals)
        last_atr = float(atr.fillna(0).iloc[-1]) or (last_price * 0.0015)

        # تحديد وضع بولينجر بالتفصيل
        if last_price <= last_lower:
            bb_status = "اختراق الحد السفلي (تشبع بيعي قوي) 🟢"
            bb_signal = "BUY"
        elif last_price >= last_upper:
            bb_status = "اختراق الحد العلوي (تشبع شرائي قوي) 🔴"
            bb_signal = "SELL"
        else:
            bb_status = "داخل نطاق بولينجر ↔️"
            bb_signal = "NEUTRAL"

        # حساب النقاط واعتماد بولينجر كفلتر أساسي
        buy_score = 0
        sell_score = 0

        # نقاط Bollinger Bands (وزن أعلى)
        if bb_signal == "BUY": buy_score += 3
        elif bb_signal == "SELL": sell_score += 3

        # نقاط RSI
        if last_rsi <= 35: buy_score += 2
        elif last_rsi >= 65: sell_score += 2

        # نقاط الاتجاه EMA
        if last_price > last_ema: buy_score += 1
        else: sell_score += 1

        # قرار التوصية النهائي
        if buy_score >= 4:
            signal_text = "إشارة شراء قوية (BUY)"
            signal_emoji = "🟢"
        elif sell_score >= 4:
            signal_text = "إشارة بيع قوية (SELL)"
            signal_emoji = "🔴"
        else:
            signal_text = "حالة محايدة - انتظار فرصة مؤكدة (Wait)"
            signal_emoji = "⚪"

        sl_buy = round(last_price - (last_atr * 1.5), decimals)
        tp_buy = round(last_price + (last_atr * 2.5), decimals)
        sl_sell = round(last_price + (last_atr * 1.5), decimals)
        tp_sell = round(last_price - (last_atr * 2.5), decimals)

        return {
            "symbol": symbol_key,
            "tf_label": tf_info["label"],
            "price": last_price,
            "rsi": last_rsi,
            "bb_status": bb_status,
            "ema_status": "صاعد (Above EMA)" if last_price > last_ema else "هابط (Below EMA)",
            "signal_text": signal_text,
            "signal_emoji": signal_emoji,
                        "sl_buy": sl_buy, "tp_buy": tp_buy,
            "sl_sell": sl_sell, "tp_sell": tp_sell
        }
    except Exception as e:
        return {"error": f"Error during analysis: {str(e)}"}
        
    
        
        
        

# ==================== المنبه التلقائي ====================
async def auto_alert_checker(app: Application):
    watchlist = ["🟢 EUR/USD", "🔵 GBP/USD", "🟡 الذهب (Gold)", "⚪ الفضة (Silver)", "🟠 Bitcoin", "🟩 NVIDIA", "🚗 Tesla", "🍏 Apple"]
    while True:
        try:
            await asyncio.sleep(60)
            for symbol in watchlist:
                res = analyze_asset(symbol, "5m")
                if "error" not in res and res["signal"] in ["BUY", "SELL"]:
                    alert_msg = (
                        f"🔔 **تنبيه إشارة فرصة قوية!** 🔔\n"
                        f"───────────────────\n"
                        f"📊 **الأصل:** {res['symbol']}\n"
                        f"⏱️ **الإطار:** 5 دقائق\n"
                        f"💵 **السعر:** `{res['price']}`\n"
                        f"🎯 **التوصية:** {res['signal_emoji']} **{res['signal_text']}**\n"
                        f"📈 **RSI:** `{res['rsi']}` | **Stoch:** `{res['stoch']}`\n"
                        f"📊 **MACD:** {res['macd_status']}\n"
                        f"───────────────────\n"
                        f"💡 **TP:** `{res['tp_buy'] if res['signal']=='BUY' else res['tp_sell']}` | **SL:** `{res['sl_buy'] if res['signal']=='BUY' else res['sl_sell']}`"
                    )
                    for user_id in list(SUBSCRIBED_USERS):
                        try:
                            await app.bot.send_message(chat_id=user_id, text=alert_msg, parse_mode="Markdown")
                        except Exception:
                            pass
        except Exception:
            await asyncio.sleep(10)

# ==================== الأزرار والواجهة ====================
def build_menu_keyboard(user_id: int):
    alert_status = "🔔 المنبه: مفعّل" if user_id in SUBSCRIBED_USERS else "🔕 المنبه: معطّل"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💱 جميع أزواج الفوركس", callback_data="cat_forex"), InlineKeyboardButton("📈 الأسهم العالمية", callback_data="cat_stocks")],
        [InlineKeyboardButton("🪙 السلع والمعادن", callback_data="cat_commodities"), InlineKeyboardButton("⚡ العملات الرقمية", callback_data="cat_crypto")],
        [InlineKeyboardButton(f"{alert_status} (اضغط للتغيير)", callback_data="toggle_alerts")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id if update.effective_chat else None

    reply_markup = build_menu_keyboard(chat_id)
    welcome_msg = (
        "👋 **مرحباً بك في بوت التداول الفني المتقدم**\n\n"
        "اختر القسم الذي تريد استعراض أصوله للتحليل اللحظي المباشر:"
    )
    if update.message:
        await update.message.reply_text(welcome_msg, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(welcome_msg, parse_mode="Markdown", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = query.message.chat_id

    if data == "toggle_alerts":
        if chat_id in SUBSCRIBED_USERS:
            SUBSCRIBED_USERS.remove(chat_id)
            await query.answer("🔕 تم إيقاف المنبه التلقائي لحسابك.", show_alert=True)
        else:
            SUBSCRIBED_USERS.add(chat_id)
            await query.answer("🔔 تم تفعيل المنبه التلقائي لحسابك!", show_alert=True)
        await query.message.edit_reply_markup(reply_markup=build_menu_keyboard(chat_id))

    elif data.startswith("cat_"):
        cat = data.split("cat_")[1]
        items = {}
        title = ""
        if cat == "forex":
            items, title = FOREX_PAIRS, "💱 قائمة جميع أزواج العملات (24+ زوج):"
        elif cat == "stocks":
            items, title = STOCKS, "📈 قائمة الأسهم العالمية:"
        elif cat == "commodities":
            items, title = COMMODITIES, "🪙 قائمة السلع والمعادن حية:"
        elif cat == "crypto":
            items, title = CRYPTO, "⚡ قائمة العملات الرقمية:"

        buttons = []
        keys = list(items.keys())
        for i in range(0, len(keys), 2):
            row = [InlineKeyboardButton(keys[i], callback_data=f"select_{keys[i]}")]
            if i + 1 < len(keys):
                row.append(InlineKeyboardButton(keys[i+1], callback_data=f"select_{keys[i+1]}"))
            buttons.append(row)
        buttons.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")])

        await query.message.edit_text(title, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))

    elif data.startswith("select_"):
        symbol = data.split("select_")[1]
        keyboard = [
            [
                InlineKeyboardButton("⏱️ 1 دقيقة", callback_data=f"tf_{symbol}_1m"),
                InlineKeyboardButton("⏱️ 5 دقائق", callback_data=f"tf_{symbol}_5m"),
                InlineKeyboardButton("⏱️ 15 دقيقة", callback_data=f"tf_{symbol}_15m")
            ],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]
        ]
        await query.message.edit_text(f"⏰ اختر الإطار الزمني لـ ({symbol}):", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("tf_"):
        _, symbol, tf = data.split("_")
        await query.message.edit_text(f"⏳ جاري تحليل {symbol} وحساب المؤشرات الحية...")
        res = analyze_asset(symbol, tf)

        if "error" in res:
            await query.message.edit_text(f"❌ {res['error']}")
            return

        msg = (
            f"📊 **تحليل فني متكامل لـ {res['symbol']}**\n"
            f"───────────────────\n"
            f"⏱️ **الإطار الزمني:** {res['tf_label']}\n"
            f"💵 **السعر الحالي:** `{res['price']}`\n"
            f"📈 **مؤشر RSI:** `{res['rsi']}`\n"
            f"📊 **مؤشر بولينجر:** `{res['bb_status']}`\n"  
            f"🎯 **التوصية النهائية:**\n"
            f"{res['signal_emoji']} **{res['signal_text']}**\n\n"
            f"📐 **الأهداف المقترحة (MT5):**\n"
            f"💡 **الشراء:** TP `{res['tp_buy']}` | SL `{res['sl_buy']}`\n"
            f"💡 **البيع:** TP `{res['tp_sell']}` | SL `{res['sl_sell']}`"
        )

        keyboard = [[InlineKeyboardButton("🔄 إعادة التحليل", callback_data=f"tf_{symbol}_{tf}"), InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]]
        await query.message.edit_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "main_menu":
        await start(update, context)

async def post_init(app: Application):
    asyncio.create_task(auto_alert_checker(app))

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return

    app = Application.builder().token(token).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    app.run_polling()

if __name__ == "__main__":
    main()
    
    
    
    
