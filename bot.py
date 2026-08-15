import os
import logging
import yfinance as yf
import pandas as pd
import numpy as np
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# إعداد التسجيل (Logs)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 🔑 التوكن الخاص بك
TOKEN = "8920172447:AAF0wf_-TG5G7QhV3WRJr8uzNyNS9vSHlFc"

# ---------------------------------------------------------
# 1. قائمة الأصول المالية المتاحة (Forex, OTC, Stocks, Crypto)
# ---------------------------------------------------------
ASSETS = {
    "forex": {
        "EUR/USD": "EURUSD=X",
        "GBP/USD": "GBPUSD=X",
        "USD/JPY": "JPY=X",
        "USD/CHF": "CHF=X",
        "AUD/USD": "AUDUSD=X",
        "USD/CAD": "CAD=X",
        "NZD/USD": "NZDUSD=X",
        "EUR/GBP": "EURGBP=X",
        "EUR/JPY": "EURJPY=X",
        "GBP/JPY": "GBPJPY=X"
    },
    "otc": {
        "EUR/USD OTC": "EURUSD=X",
        "GBP/USD OTC": "GBPUSD=X",
        "USD/JPY OTC": "JPY=X",
        "AUD/USD OTC": "AUDUSD=X",
        "USD/CAD OTC": "CAD=X",
        "EUR/JPY OTC": "EURJPY=X",
        "GBP/JPY OTC": "GBPJPY=X",
        "USD/CHF OTC": "CHF=X"
    },
    "stocks": {
        "Apple (AAPL)": "AAPL",
        "Tesla (TSLA)": "TSLA",
        "Microsoft (MSFT)": "MSFT",
        "Google (GOOGL)": "GOOGL",
        "Amazon (AMZN)": "AMZN",
        "NVIDIA (NVDA)": "NVDA",
        "Meta (META)": "META"
    },
    "crypto": {
        "Bitcoin (BTC/USD)": "BTC-USD",
        "Ethereum (ETH/USD)": "ETH-USD",
        "Binance Coin (BNB/USD)": "BNB-USD",
        "Ripple (XRP/USD)": "XRP-USD",
        "Solana (SOL/USD)": "SOL-USD",
        "Cardano (ADA/USD)": "ADA-USD",
        "Dogecoin (DOGE/USD)": "DOGE-USD"
    }
}

# ---------------------------------------------------------
# 2. خوارزمية التحليل الفني (RSI + EMA + Bollinger Bands)
# ---------------------------------------------------------
def analyze_market(ticker_symbol, timeframe='5m'):
    try:
        # جلب البيانات
        data = yf.download(tickers=ticker_symbol, period='1d', interval=timeframe, progress=False)
        if len(data) < 20:
            data = yf.download(tickers=ticker_symbol, period='5d', interval=timeframe, progress=False)
        
        if data.empty:
            return "عذراً، تعذر جلب البيانات الحالية لهذا الأصل."

        # حساب سعر الإغلاق
        close = data['Close'].squeeze()

        # 1. حساب RSI (14)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = float(rsi.iloc[-1])

        # 2. حساب EMA (9, 21)
        ema9 = float(close.ewm(span=9, adjust=False).mean().iloc[-1])
        ema21 = float(close.ewm(span=21, adjust=False).mean().iloc[-1])

        # 3. حساب Bollinger Bands (20, 2)
        sma20 = close.rolling(window=20).mean()
        std20 = close.rolling(window=20).std()
        upper_band = float((sma20 + (std20 * 2)).iloc[-1])
        lower_band = float((sma20 - (std20 * 2)).iloc[-1])
        current_price = float(close.iloc[-1])

        # منطق التوصية والاتجاه
        signal = "NEUTRAL"
        trend_desc = "اتجاه محايد / تذبذب ⚪"

        # شرط الشراء (BUY): اختراق النطاق السفلي للبولينجر + تقاطع صاعد + RSI مشبع بيعياً
        if current_price <= lower_band or (ema9 > ema21 and current_rsi < 60):
            signal = "BUY"
            trend_desc = "اتجاه صاعد (BUY) 🟢"
        # شرط البيع (SELL): اختراق النطاق العلوي للبولينجر + تقاطع هابط + RSI مشبع شرائياً
        elif current_price >= upper_band or (ema9 < ema21 and current_rsi > 40):
            signal = "SELL"
            trend_desc = "اتجاه هابط (SELL) 🔴"

        return {
            "rsi": round(current_rsi, 2),
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
# 3. معالجات الأوامر والأزرار (Telegram UI)
# ---------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌐 فوركس (Forex)", callback_data='cat_forex'), InlineKeyboardButton("⚡ سوق OTC", callback_data='cat_otc')],
        [InlineKeyboardButton("📈 الأسهم (Stocks)", callback_data='cat_stocks'), InlineKeyboardButton("⚡ العملات الرقمية (Crypto)", callback_data='cat_crypto')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = "مرحباً بك في بوت التوصيات المتقدم 🎯\nيرجى اختيار القسم الذي تريد التداول عليه:"
    
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
        row.append(InlineKeyboardButton(name, callback_data=f"select_{symbol}_{name}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='main_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("اختر الزوج أو الأصل المالي للحصول على التوصية:", reply_markup=reply_markup)

async def send_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("جاري تحليل الأسواق والمؤشرات...")
    
    parts = query.data.split('_')
    symbol = parts[1]
    name = parts[2]
    timeframe = parts[3] if len(parts) > 3 else '5m'
    
    result = analyze_market(symbol, timeframe)
    
    if not result or isinstance(result, str):
        await query.edit_message_text(
            "⚠️ تعذر جلب البيانات لهذا الأصل حالياً، يرجى المحاولة لاحقاً.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='main_menu')]])
        )
        return

    tf_display = "M5" if timeframe == '5m' else "M1" if timeframe == '1m' else "M15"
    
    if result['signal'] == "BUY":
        rec_text = "🎯 التوصية: 🟢 CALL / BUY (شراء قوي)"
    elif result['signal'] == "SELL":
        rec_text = "🎯 التوصية: 🔴 PUT / SELL (بيع قوي)"
    else:
        rec_text = "🎯 التوصية: ⚪ WAIT (انتظار / تذبذب)"

    text = (
        f"📡 **الأصل:** {name}\n"
        f"⏱️ **الإطار الزمني:** {tf_display}\n"
        f"📊 **تحليل الاتجاه:** {result['trend']}\n"
        f"⚙️ **المؤشرات:** RSI ({result['rsi']}) | Bollinger Bands | EMA\n"
        f"💵 **السعر الحالي:** {result['price']}\n\n"
        f"{rec_text}"
    )

    keyboard = [
        [InlineKeyboardButton("🔄 تحديث التوصية", callback_data=f"select_{symbol}_{name}_{timeframe}")],
        [
            InlineKeyboardButton("⏱️ M1", callback_data=f"select_{symbol}_{name}_1m"),
            InlineKeyboardButton("⏱️ M5", callback_data=f"select_{symbol}_{name}_5m"),
            InlineKeyboardButton("⏱️ M15", callback_data=f"select_{symbol}_{name}_15m")
        ],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data='main_menu')]
    ]
    
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

# ---------------------------------------------------------
# 4. تشغيل التطبيق (Main)
# ---------------------------------------------------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern='^main_menu$'))
    app.add_handler(CallbackQueryHandler(handle_category, pattern='^cat_'))
    app.add_handler(CallbackQueryHandler(send_signal, pattern='^select_'))

    print("🤖 Bot is running successfully...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
        
    
    
    

    
    
    
    
    
    
    
    
    
    
    
    
