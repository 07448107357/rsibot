import os
import yfinance as yf
import pandas as pd
import numpy as np
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ==================== موسوعة الأصول والشاشات الشاملة ====================
SYMBOL_MAP = {
    # الفوركس الرئيسي والفرعي (Spot Forex =X)
    "EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "JPY=X",
    "USD/CAD": "CAD=X", "AUD/USD": "AUDUSD=X", "USD/CHF": "CHF=X",
    "NZD/USD": "NZDUSD=X", "EUR/GBP": "EURGBP=X", "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X", "EUR/CAD": "EURCAD=X", "EUR/AUD": "EURAUD=X",
    "EUR/CHF": "EURCHF=X", "GBP/CAD": "GBPCAD=X", "GBP/AUD": "GBPAUD=X",
    "GBP/CHF": "GBPCHF=X", "AUD/CAD": "AUDCAD=X", "AUD/JPY": "AUDJPY=X",
    "AUD/NZD": "AUDNZD=X", "NZD/JPY": "NZDJPY=X", "CAD/JPY": "CADJPY=X",
    "CHF/JPY": "CHFJPY=X",
    
    # السلع والمعادن (Spot Metals)
    "الذهب (Gold)": "XAUUSD=X", "الفضة (Silver)": "XAGUSD=X", "النفط (Oil)": "CL=F",
    
    # العملات الرقمية
    "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Solana": "SOL-USD", 
    "Binance Coin": "BNB-USD", "XRP": "XRP-USD", "Cardano": "ADA-USD",
    
    # الأسهم العالمية الكبرى
    "Apple": "AAPL", "Tesla": "TSLA", "NVIDIA": "NVDA", "Amazon": "AMZN", 
    "Microsoft": "MSFT", "Netflix": "NFLX", "Google": "GOOGL", "Meta": "META"
}

TIMEFRAME_MAP = {
    "1m": {"interval": "1m", "period": "1d", "label": "دقيقة واحدة (1m)"},
    "5m": {"interval": "5m", "period": "5d", "label": "5 دقائق (5m)"},
    "15m": {"interval": "15m", "period": "5d", "label": "15 دقيقة (15m)"}
}

SUBSCRIBED_USERS = set()

# ==================== دالّات التحليل الفني ====================
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

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    true_range = np.max(pd.concat([high_low, high_close, low_close], axis=1), axis=1)
    return true_range.rolling(period).mean()

def analyze_asset(symbol_key: str, tf_key: str = "5m") -> dict:
    ticker = SYMBOL_MAP.get(symbol_key, symbol_key)
    tf_info = TIMEFRAME_MAP.get(tf_key, TIMEFRAME_MAP["5m"])
    
    try:
        df = yf.download(tickers=ticker, period=tf_info["period"], interval=tf_info["interval"], progress=False)
        if df.empty or len(df) < 50:
            return {"error": "بيانات التداول غير متوفرة لهذا الأسلوب/الإطار حالياً."}

        close = df['Close'][ticker] if isinstance(df.columns, pd.MultiIndex) else df['Close']
        high = df['High'][ticker] if isinstance(df.columns, pd.MultiIndex) else df['High']
        low = df['Low'][ticker] if isinstance(df.columns, pd.MultiIndex) else df['Low']

        rsi = calculate_rsi(close, 14)
        upper_band, lower_band, sma20 = calculate_bollinger_bands(close, 20, 2)
        ema50 = close.ewm(span=50, adjust=False).mean()
        atr = calculate_atr(pd.DataFrame({'High': high, 'Low': low, 'Close': close}), 14)

        is_forex = "=X" in ticker and "XAU" not in ticker and "XAG" not in ticker
        decimals = 5 if is_forex else 2

        last_price = round(float(close.iloc[-1]), decimals)
        last_rsi = round(float(rsi.fillna(50).iloc[-1]), 2)
        last_ema = round(float(ema50.iloc[-1]), decimals)
        last_upper = round(float(upper_band.fillna(last_price).iloc[-1]), decimals)
        last_lower = round(float(lower_band.fillna(last_price).iloc[-1]), decimals)
        last_atr = float(atr.fillna(0).iloc[-1])

        if last_atr == 0:
            last_atr = last_price * 0.0015

        sl_buy = round(last_price - (last_atr * 1.5), decimals)
        tp_buy = round(last_price + (last_atr * 2.5), decimals)
        sl_sell = round(last_price + (last_atr * 1.5), decimals)
        tp_sell = round(last_price - (last_atr * 2.5), decimals)

        trend = "صاعد (Above EMA)" if last_price > last_ema else "هابط (Below EMA)"

        if last_price >= last_upper:
            bb_state = "أعلى Bollinger Band (فرصة ارتداد هابط)"
        elif last_price <= last_lower:
            bb_state = "أسفل Bollinger Band (فرصة ارتداد صاعد)"
        else:
            bb_state = "داخل Bollinger Bands"

        signal = "WAIT"
        signal_text = "حالة محايدة (Wait / No Trade)"
        signal_emoji = "⚪"

        if last_rsi < 32 and last_price <= last_lower:
            signal = "BUY"
            signal_text = "إشارة شراء (BUY)"
            signal_emoji = "🟢"
        elif last_rsi > 68 and last_price >= last_upper:
            signal = "SELL"
            signal_text = "إشارة بيع (SELL)"
            signal_emoji = "🔴"

        return {
            "symbol": symbol_key,
            "tf_label": tf_info["label"],
            "price": last_price,
            "rsi": last_rsi,
            "trend": trend,
            "bb_state": bb_state,
            "signal": signal,
            "signal_text": signal_text,
            "signal_emoji": signal_emoji,
            "sl_buy": sl_buy,
            "tp_buy": tp_buy,
            "sl_sell": sl_sell,
            "tp_sell": tp_sell
        }
    except Exception as e:
        return {"error": f"حدث خطأ أثناء تحليل البيانات: {str(e)}"}

# ==================== نظام التنبيهات المنبه الآلي المتكامل ====================
async def auto_alert_checker(app: Application):
    # قائمة المراقبة الموسعة للتنبيهات التلقائية
    watchlist = [
        "EUR/USD", "GBP/USD", "USD/JPY", "GBP/JPY",
        "الذهب (Gold)", "الفضة (Silver)", "النفط (Oil)",
        "Bitcoin", "Ethereum", "Solana",
        "Apple", "Tesla", "NVIDIA", "Amazon", "Netflix", "Google"
    ]
    
    while True:
        try:
            await asyncio.sleep(60) # فحص كل دقيقة
            for symbol in watchlist:
                res = analyze_asset(symbol, "5m")
                if "error" not in res and res["signal"] in ["BUY", "SELL"]:
                    alert_msg = (
                        f"🔔 **تنبيه إشارة تداول جديدة!** 🔔\n"
                        f"───────────────────\n"
                        f"📊 **الأصل:** {res['symbol']}\n"
                        f"⏱️ **الإطار:** 5 دقائق\n"
                        f"💵 **السعر:** `{res['price']}`\n"
                        f"🎯 **التوصية:** {res['signal_emoji']} **{res['signal_text']}**\n"
                        f"📈 **RSI:** `{res['rsi']}`\n"
                        f"───────────────────\n"
                        f"💡 **TP:** `{res['tp_buy'] if res['signal']=='BUY' else res['tp_sell']}` | **SL:** `{res['sl_buy'] if res['signal']=='BUY' else res['sl_sell']}`"
                    )
                    for user_id in list(SUBSCRIBED_USERS):
                        try:
                            await app.bot.send_message(chat_id=user_id, text=alert_msg, parse_mode="Markdown")
                        except Exception:
                            pass
        except Exception as e:
            await asyncio.sleep(10)

# ==================== قوائم الأزرار والواجهة ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat:
        SUBSCRIBED_USERS.add(update.effective_chat.id)

    keyboard = [
        [InlineKeyboardButton("🏆 EUR/USD", callback_data="select_EUR/USD"), InlineKeyboardButton("🏆 GBP/USD", callback_data="select_GBP/USD")],
        [InlineKeyboardButton("🪙 الذهب (Gold)", callback_data="select_الذهب (Gold)"), InlineKeyboardButton("🥈 الفضة (Silver)", callback_data="select_الفضة (Silver)")],
        [InlineKeyboardButton("⚡ Bitcoin", callback_data="select_Bitcoin"), InlineKeyboardButton("⚡ Ethereum", callback_data="select_Ethereum")],
        [InlineKeyboardButton("🍎 Apple", callback_data="select_Apple"), InlineKeyboardButton("🚗 Tesla", callback_data="select_Tesla")],
        [InlineKeyboardButton("🌐 باقي الأزواج والأسهم والعملات", callback_data="more_assets")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_msg = (
        "👋 **أهلاً بك في بوت التحليل المتقدم للأسواق العالمية**\n\n"
        "🔔 *تم تفعيل نظام المنبه الآلي للتنبيهات تلقائياً لحسابك!*\n"
        "اختر الزوج أو الأصل الذي تريد تحليله مباشرة:"
    )
    if update.message:
        await update.message.reply_text(welcome_msg, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(welcome_msg, parse_mode="Markdown", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "more_assets":
        keyboard = [
            [InlineKeyboardButton("📊 USD/JPY", callback_data="select_USD/JPY"), InlineKeyboardButton("📊 GBP/JPY", callback_data="select_GBP/JPY")],
            [InlineKeyboardButton("📊 AUD/USD", callback_data="select_AUD/USD"), InlineKeyboardButton("📊 USD/CAD", callback_data="select_USD/CAD")],
            [InlineKeyboardButton("💚 Solana", callback_data="select_Solana"), InlineKeyboardButton("💚 XRP", callback_data="select_XRP")],
            [InlineKeyboardButton("💻 NVIDIA", callback_data="select_NVIDIA"), InlineKeyboardButton("📦 Amazon", callback_data="select_Amazon")],
            [InlineKeyboardButton("🎬 Netflix", callback_data="select_Netflix"), InlineKeyboardButton("🔍 Google", callback_data="select_Google")],
            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]
        ]
        await query.message.edit_text("🌐 **اختر من قائمة الأصول والأسهم الإضافية:**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

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
        await query.message.edit_text(f"⏰ اختر الإطار الزمني للتحليل الخاص بـ ({symbol}):", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("tf_"):
        _, symbol, tf = data.split("_")
        await query.message.edit_text(f"⏳ جاري تحليل {symbol}...")
        res = analyze_asset(symbol, tf)

        if "error" in res:
            await query.message.edit_text(f"❌ {res['error']}")
            return

        msg = (
            f"📊 **تحليل متقدم لـ {res['symbol']}**\n"
            f"───────────────────\n"
            f"⏱️ **الإطار الزمني:** {res['tf_label']}\n"
            f"💵 **السعر الحالي:** `{res['price']}`\n"
            f"📈 **قيمة RSI:** `{res['rsi']}`\n"
            f"📉 **الاتجاه العام (EMA 50):** {res['trend']}\n"
            f"🎯 **حالة بولينجر:** {res['bb_state']}\n"
            f"───────────────────\n"
            f"🎯 **التوصية:**\n"
            f"{res['signal_emoji']} **{res['signal_text']}**\n\n"
            f"📐 **المستويات المقترحة (MT5):**\n"
            f"💡 **مستويات الشراء:** TP `{res['tp_buy']}` | SL `{res['sl_buy']}`\n"
            f"💡 **مستويات البيع:** TP `{res['tp_sell']}` | SL `{res['sl_sell']}`"
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
        print("❌ Error: TELEGRAM_BOT_TOKEN environment variable is missing!")
        return

    app = Application.builder().token(token).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))

    print("🚀 Bot is running with auto-alerts and full asset map...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
    
    
    
    
    
    
    
    
