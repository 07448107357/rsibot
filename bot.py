import os
import yfinance as yf
import pandas as pd
import numpy as np
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ==================== Map Telegram symbols to yfinance symbols ====================
# تم ضبط جميع الرموز المباشرة (Spot) لترتيبها مع البورصة العالمية
SYMBOL_MAP = {
    # Forex Pairs (Standardised to Spot Forex =X)
    "EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "JPY=X",
    "USD/CAD": "CAD=X", "AUD/USD": "AUDUSD=X", "USD/CHF": "CHF=X",
    "NZD/USD": "NZDUSD=X", "EUR/GBP": "EURGBP=X", "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X", "EUR/CAD": "EURCAD=X", "EUR/AUD": "EURAUD=X",
    "EUR/CHF": "EURCHF=X", "GBP/CAD": "GBPCAD=X", "GBP/AUD": "GBPAUD=X",
    "GBP/CHF": "GBPCHF=X", "AUD/CAD": "AUDCAD=X", "AUD/JPY": "AUDJPY=X",
    "AUD/NZD": "AUDNZD=X", "NZD/JPY": "NZDJPY=X", "CAD/JPY": "CADJPY=X",
    "CHF/JPY": "CHFJPY=X",
    
    # Commodities & Cryptos (Spot Gold & Silver)
    "الذهب (Gold)": "XAUUSD=X", "الفضة (Silver)": "XAGUSD=X", "النفط (Crude Oil)": "CL=F",
    "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD",
    
    # Direct short codes
    "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "USDJPY": "JPY=X",
    "USDCAD": "CAD=X", "USDCHF": "CHF=X", "AUDUSD": "AUDUSD=X",
    "NZDUSD": "NZDUSD=X", "EURGBP": "EURGBP=X", "EURJPY": "EURJPY=X",
    "GBPJPY": "GBPJPY=X", "XAUUSD": "XAUUSD=X", "XAGUSD": "XAGUSD=X",
    "BTC": "BTC-USD", "ETH": "ETH-USD"
}

# Timeframe mapping
TIMEFRAME_MAP = {
    "1m": {"interval": "1m", "period": "1d", "label": "دقيقة واحدة (1m)"},
    "5m": {"interval": "5m", "period": "5d", "label": "5 دقائق (5m)"},
    "15m": {"interval": "15m", "period": "5d", "label": "15 دقيقة (15m)"}
}

# ==================== Technical Analysis Functions ====================
def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_bollinger_bands(series: pd.Series, period: int = 20, std_dev: int = 2):
    sma = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band, lower_band, sma

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift())
    low_close = np.abs(df['Low'] - df['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    return true_range.rolling(period).mean()

def analyze_asset(symbol_key: str, tf_key: str = "5m") -> dict:
    ticker = SYMBOL_MAP.get(symbol_key, symbol_key)
    tf_info = TIMEFRAME_MAP.get(tf_key, TIMEFRAME_MAP["5m"])
    
    try:
        df = yf.download(tickers=ticker, period=tf_info["period"], interval=tf_info["interval"], progress=False)
        if df.empty or len(df) < 50:
            return {"error": "بيانات التداول غير متوفرة لهذا الأسلوب/الإطار حالياً."}

        if isinstance(df.columns, pd.MultiIndex):
            close = df['Close'][ticker]
            high = df['High'][ticker]
            low = df['Low'][ticker]
        else:
            close = df['Close']
            high = df['High']
            low = df['Low']

        rsi = calculate_rsi(close, 14)
        upper_band, lower_band, sma20 = calculate_bollinger_bands(close, 20, 2)
        ema50 = close.ewm(span=50, adjust=False).mean()
        atr = calculate_atr(pd.DataFrame({'High': high, 'Low': low, 'Close': close}), 14)

        # تحديد الدقة العشرية ديناميكياً (5 أرقام بالفوركس، ورقمين للذهب/البيتكوين)
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

# ==================== Telegram Handlers ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🏆 EUR/USD", callback_data="select_EUR/USD"), InlineKeyboardButton("🏆 GBP/USD", callback_data="select_GBP/USD")],
        [InlineKeyboardButton("🪙 الذهب (XAUUSD)", callback_data="select_XAUUSD"), InlineKeyboardButton("🥈 الفضة (XAGUSD)", callback_data="select_XAGUSD")],
        [InlineKeyboardButton("⚡ Bitcoin", callback_data="select_BTC"), InlineKeyboardButton("⚡ Ethereum", callback_data="select_ETH")],
        [InlineKeyboardButton("📊 USD/JPY", callback_data="select_USD/JPY"), InlineKeyboardButton("📊 AUD/USD", callback_data="select_AUD/USD")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_msg = (
        "👋 **أهلاً بك في بوت التحليل المتقدم للأسواق العالمية**\n\n"
        "اختر الزوج أو الأصل الذي تريد تحليله مباشرة وفق أسعار البورصة العالمية:"
    )
    if update.message:
        await update.message.reply_text(welcome_msg, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(welcome_msg, parse_mode="Markdown", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("select_"):
        symbol = data.split("select_")[1]
        keyboard = [
            [
                InlineKeyboardButton("⏱️ 1 دقيقة", callback_data=f"tf_{symbol}_1m"),
                InlineKeyboardButton("⏱️ 5 دقائق", callback_data=f"tf_{symbol}_5m"),
                InlineKeyboardButton("⏱️ 15 دقيقة", callback_data=f"tf_{symbol}_15m")
            ],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(f"⏰ اختر الإطار الزمني للتحليل الخاص بـ ({symbol}):", reply_markup=reply_markup)

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

        keyboard = [[InlineKeyboardButton("🔄 إعادة التحليل", callback_data=f"select_{symbol}"), InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(msg, parse_mode="Markdown", reply_markup=reply_markup)

    elif data == "main_menu":
        await start(update, context)

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ Error: TELEGRAM_BOT_TOKEN environment variable is missing!")
        return

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))

    print("🚀 Bot is running successfully...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
    
    
    
    
    
    
    
