import random
import requests
import pandas as pd
import numpy as np
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import requests
import os
import random
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import pandas as pd
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# --- خادم ويب وهمي لإرضاء منصة Render ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_web():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_web, daemon=True).start()

# --- القوائم والأزواج الكاملة مع إضافة العملات والأزواج السويسرية ---
CATEGORIES = {
    "💱 العملات (Forex)": [
        "🇬🇧🇺🇸 GBP/USD OTC", "🇧🇭🇨🇳 BHD/CNY OTC",
        "🇺🇦🇺🇸 UAH/USD OTC", "🇧🇩🇺🇸 USD/BDT OTC",
        "🇻🇳🇺🇸 USD/VND OTC", "🇨🇴🇺🇸 USD/COP OTC",
        "🇪🇺🇯🇵 EUR/JPY OTC", "🇩🇿🇺🇸 USD/DZD OTC",
        "🇨🇦🇺🇸 USD/CAD OTC", "🇱🇧🇺🇸 LBP/USD OTC",
        "🇪🇺🇺🇸 EUR/USD OTC", "🇬🇧🇪🇺 EUR/GBP OTC",
        "🇳🇿🇪🇺 EUR/NZD OTC", "🇷🇺🇺🇸 USD/RUB OTC",
        "🇨🇦🇦🇺 AUD/CAD OTC", "🇯🇵🇦🇺 AUD/JPY OTC",
        "🇦🇷🇺🇸 USD/ARS OTC", "🇲🇾🇺🇸 USD/MYR OTC",
        "🇯🇵🇨🇦 CAD/JPY OTC", "🇨🇭🇳🇴 CHF/NOK OTC",
        "🇧🇷🇺🇸 USD/BRL OTC", "🇲🇽🇺🇸 USD/MXN OTC",
        "🇨🇭🇺🇸 USD/CHF OTC", "🇨🇭🇯🇵 CHF/JPY OTC",
        "🇪🇺🇨🇭 EUR/CHF OTC", "🇮🇳🇺🇸 USD/INR OTC",
        "🇦🇺🇳🇿 AUD/NZD OTC", "🇯🇴🇨🇳 JOD/CNY OTC",
        "🇲🇦🇪🇸 MAD/USD OTC", "🇮🇩🇺🇸 USD/IDR OTC",
        "🇹🇭🇺🇸 USD/THB OTC", "🇵🇰🇺🇸 USD/PKR OTC",
        "🇰🇪🇺🇸 KES/USD OTC", "🇦🇪🇨🇳 AED/CNY OTC",
        "🇳🇬🇺🇸 NGN/USD OTC", "🇨🇱🇺🇸 USD/CLP OTC",
        "🇸🇬🇺🇸 USD/SGD OTC", "🇸🇦🇨🇳 SAR/CNY OTC",
        "🇨🇳🇺🇸 USD/CNH OTC", "🇶🇦🇨🇳 QAR/CNY OTC",
        "🇳🇿🇺🇸 NZD/USD OTC",
        # الأزواج السويسرية الإضافية بدقة
        "🇬🇧🇨🇭 GBP/CHF OTC", "🇦🇺🇨🇭 AUD/CHF OTC",
        "🇳🇿🇨🇭 NZD/CHF OTC"
    ],
    "🟡 العملات الرقمية (Crypto)": [
        "🗿 Bitcoin ETF OTC", "🥈 Litecoin OTC",
        "🔗 Chainlink OTC", "💎 Toncoin OTC",
        "🟣 Polygon OTC", "🔴 Polkadot OTC",
        "🟡 BNB OTC", "🔴 TRON OTC",
        "🟣 Solana OTC", "🟠 Bitcoin OTC",
        "🟡 Dogecoin OTC", "🔵 Cardano OTC",
        "🔷 Dash OTC", "🔺 Avalanche OTC"
    ],
    "📈 الأسهم والشركات (Stocks)": [
        "✈️ Boeing OTC", "📱 Facebook OTC",
        "🥤 ExxonMobil OTC", "💻 AMD OTC",
        "📦 Amazon OTC", "🛒 Alibaba OTC",
        "⛏️ Marathon Digital OTC", "📊 VIX OTC",
        "💳 VISA OTC", "🎬 Netflix OTC",
        "🍔 McDonald's OTC", "📦 FedEx OTC",
        "💻 Microsoft OTC", "💊 Pfizer OTC",
        "🍏 Apple OTC", "🪙 Coinbase OTC",
        "🚗 Tesla OTC", "🌐 Cisco OTC",
        "🏦 Citigroup OTC", "👁️ Palantir OTC",
        "🟦 Intel OTC"
    ]
}

TIMEFRAMES = ["5s", "10s", "15s", "30s", "1m", "5m", "15m", "30m", "1h"]

import pandas as pd
import numpy as np

# ==========================================================
# القسم 3: الدالة الرئيسية analyze_market
# ==========================================================
def analyze_market(name: str, timeframe: str = "15m") -> dict:
    timeframe: TIMEFRAME_MAP
    try:
        if timeframe not in TIMEFRAME_MAP:
            return {"error": f"فريم غير مدعوم: {timeframe}. الفريمات المتاحة: {', '.join(TIMEFRAME_MAP.keys())}"}
        symbol = name.upper().replace("-", "/")
        if "/" not in symbol:
            return {"error": "صيغة الرمز غير صحيحة. استخدم مثل: EUR/USD أو GBP/USD"}
        df = fetch_forex_klines(symbol, timeframe, size=200)
        if len(df) < MIN_CANDLES_REQUIRED:
            return {"error": f"بيانات غير كافية ({len(df)} شمعة فقط) لحساب المؤشرات بدقة."}
        current_rsi = calculate_rsi(df, period=14)
        ema_fast = calculate_ema(df, period=9)
        ema_slow = calculate_ema(df, period=21)
        macd_data = calculate_macd(df)
        last_price = float(df["close"].iloc[-1])
        overall = build_recommendation(current_rsi, macd_data, ema_fast, ema_slow)
        cross_text = {
            "bullish_cross": "↗️ تقاطع صعودي جديد",
            "bearish_cross": "↘️ تقاطع هبوطي جديد",
            "none": "بدون تقاطع جديد",
        }[macd_data["cross"]]
        desc = (
            f"📈 الزوج: {symbol}\n"
            f"⏱️ الفريم: {timeframe}\n"
            f"💰 آخر سعر: {last_price}\n\n"
            f"— RSI (14): {current_rsi}\n"
            f"— EMA9: {ema_fast} | EMA21: {ema_slow} "
            f"({'EMA9 فوق EMA21' if ema_fast > ema_slow else 'EMA9 تحت EMA21'})\n"
            f"— MACD: {macd_data['macd']} | خط الإشارة: {macd_data['signal']} "
            f"| الهيستوغرام: {macd_data['histogram']} ({cross_text})\n\n"
            f"{overall}\n\n"
            f"⚠️ تنويه: تحليل آلي لثلاثة مؤشرات فنية (RSI, EMA, MACD)، وليس "
            f"توصية استثمارية. تداول الفوركس بالرافعة المالية ينطوي على "
            f"مخاطر عالية."
        )
        return {
            "desc": desc, "rsi": current_rsi, "ema_fast": ema_fast,
            "ema_slow": ema_slow, "macd": macd_data, "price": last_price,
        }

    except requests.exceptions.RequestException as e:
        return {"error": f"تعذر الاتصال بمزود البيانات: {str(e)}"}
    except ValueError as e:
        return {"error": str(e)}
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"حدث خطأ أثناء التحليل: {str(e)}"}


# ==========================================================
# القسم 2: المؤشرات الفنية (RSI, EMA, MACD)
# ==========================================================
def calculate_rsi(df: pd.DataFrame, period: int = 14) -> float:
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(float(rsi.iloc[-1]), 2)
def calculate_ema(df: pd.DataFrame, period: int) -> float:
    ema = df["close"].ewm(span=period, adjust=False).mean()
    return round(float(ema.iloc[-1]), 5)
def calculate_macd(df: pd.DataFrame, fast=12, slow=26, signal=9):
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    current_macd = round(float(macd_line.iloc[-1]), 5)
    current_signal = round(float(signal_line.iloc[-1]), 5)
    current_hist = round(float(histogram.iloc[-1]), 5)
    prev_hist = float(histogram.iloc[-2])
    if prev_hist <= 0 < current_hist:
        cross = "bullish_cross"
    elif prev_hist >= 0 > current_hist:
        cross = "bearish_cross"
    else:
        cross = "none"

    return {"macd": current_macd, "signal": current_signal, "histogram": current_hist, "cross": cross}


def build_recommendation(rsi: float, macd_data: dict, ema_fast: float, ema_slow: float) -> str:
    votes = []
    if rsi <= 30:
        votes.append("buy")
    elif rsi >= 70:
        votes.append("sell")

    if macd_data["cross"] == "bullish_cross" or macd_data["histogram"] > 0:
        votes.append("buy")
    elif macd_data["cross"] == "bearish_cross" or macd_data["histogram"] < 0:
        votes.append("sell")

    votes.append("buy" if ema_fast > ema_slow else "sell")

    buy_votes, sell_votes = votes.count("buy"), votes.count("sell")
    if buy_votes > sell_votes:
        return "🟢 الاتجاه العام للمؤشرات: ميل شرائي"
    elif sell_votes > buy_votes:
        return "🔴 الاتجاه العام للمؤشرات: ميل بيعي"
    return "⚪ الاتجاه العام للمؤشرات: متضارب / محايد"
    
  # ==========================================================
# القسم 3: تجميع كل شيء في إشارة واحدة جاهزة للعرض
# ==========================================================
def get_signal(name: str, timeframe: str = "15m") -> dict:
    
    timeframe: TIMEFRAME_MAP
    try:
        symbol = name.replace("/", "").replace("-", "").upper()
        df = fetch_binance_klines(symbol, timeframe, limit=200)
        if len(df) < 35:
            return {"error": "بيانات غير كافية لحساب المؤشرات (خصوصًا MACD)."}
        current_rsi = calculate_rsi(df, period=14)
        ema_fast = calculate_ema(df, period=9)
        ema_slow = calculate_ema(df, period=21)
        macd_data = calculate_macd(df)
        last_price = float(df["close"].iloc[-1])
        overall = build_recommendation(current_rsi, macd_data, ema_fast, ema_slow)
        cross_text = {
            "bullish_cross": "↗️ تقاطع صعودي جديد",
            "bearish_cross": "↘️ تقاطع هبوطي جديد",
            "none": "بدون تقاطع جديد",
        }[macd_data["cross"]]
        desc = (
            f"📈 الأصل: {symbol}\n"
            f"⏱️ الفريم: {timeframe}\n"
            f"💰 آخر سعر إغلاق: {last_price}\n\n"
            f"— RSI (14): {current_rsi}\n"
            f"— EMA9: {ema_fast} | EMA21: {ema_slow} "
            f"({'EMA9 فوق EMA21' if ema_fast > ema_slow else 'EMA9 تحت EMA21'})\n"
            f"— MACD: {macd_data['macd']} | خط الإشارة: {macd_data['signal']} "
            f"| الهيستوغرام: {macd_data['histogram']} ({cross_text})\n\n"
            f"{overall}\n\n"
            f"⚠️ تنويه: هذا تحليل آلي لثلاثة مؤشرات فنية شائعة (RSI, EMA, MACD)، "
            f"وليس توصية استثمارية. التداول ينطوي على مخاطر، والمؤشرات الفنية "
            f"قد تتعارض أو تتأخر عن حركة السعر الفعلية."
        )
        return {
            "desc": desc,
            "rsi": current_rsi,
            "ema_fast": ema_fast,
            "ema_slow": ema_slow,
            "macd": macd_data,
            "price": last_price,
        }

    except requests.exceptions.HTTPError as e:
        return {"error": f"رمز غير صحيح أو خطأ من Binance: {str(e)}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"تعذر الاتصال بـ Binance: {str(e)}"}
    except Exception as e:
        return {"error": f"حدث خطأ أثناء التحليل: {str(e)}"}      



df = fetch_forex_klines(symbol, timeframe, size=200)
if len(df) < MIN_CANDLES_REQUIRED:
    try:
            data_points = 50
            np.random.seed()
            prices = 100 + np.cumsum(np.random.normal(0, 1, data_points))
            df = pd.DataFrame({"close": prices})
    return df, None
    except Exception as e:
        return None, f"error: {str(e)}"
        
            

# =====================================================================
# واجهة تليجرام
# =====================================================================

# =====================================================================
# مطابقة المفاتيح تماماً لما هو موجود في صورة الكود لديك
# =====================================================================

CATEGORY_LABELS = {
    "💱 العملات (Forex)": "💱 العملات (Forex)",
    "🟡 العملات الرقمية (Crypto)": "🟡 العملات الرقمية (Crypto)",
    "📈 الأسهم والشركات (Stocks)": "📈 الأسهم والشركات (Stocks)"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # إنشاء الأزرار بحيث يكون الـ callback_data مطابقاً تماماً لنص المفتاح في CATEGORIES
    keyboard = [[InlineKeyboardButton(label, callback_data=f"cat_{key}")]
                for key, label in CATEGORY_LABELS.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = "🤖 **بوت الإشارات الفنية**\n\nاختر السوق المطلوب:"

    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.edit_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("cat_"):
        market_key = data.replace("cat_", "")
        
        # جلب القائمة من قاموس CATEGORIES الموجود في كودك بناءً على المفتاح المطابق تماماً
        symbols = CATEGORIES.get(market_key, [])
        context.user_data["current_market"] = market_key

        if not symbols:
            await query.message.edit_text(f"⚠️ عذراً، لم يتم العثور على أصول لهذا القسم.")
            return

        keyboard = []
        for i in range(0, len(symbols), 2):
            row = [InlineKeyboardButton(symbols[i], callback_data=f"sym_{symbols[i]}")]
            if i + 1 < len(symbols):
                row.append(InlineKeyboardButton(symbols[i + 1], callback_data=f"sym_{symbols[i + 1]}"))
            keyboard.append(row)
            
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # تنظيف اسم القسم لعرضه بشكل جميل
        clean_label = market_key
        await query.message.edit_text(f"📁 {clean_label}\nاختر الأصل:", reply_markup=reply_markup)

    elif data == "main_menu":
        await start(update, context)

    elif data.startswith("sym_"):
        symbol_name = data.replace("sym_", "")
        context.user_data["selected_symbol"] = symbol_name

        keyboard = []
        row = []
        for tf in TIMEFRAMES:
            row.append(InlineKeyboardButton(tf, callback_data=f"tf_{tf}"))
            if len(row) == 4:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
            
        market_key = context.user_data.get("current_market", "💱 العملات (Forex)")
        keyboard.append([InlineKeyboardButton("🔙 رجوع للقائمة", callback_data=f"cat_{market_key}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(f"⏱️ اختر الفريم الزمني لـ *{symbol_name}*:",
                                       reply_markup=reply_markup, parse_mode="Markdown")

    elif data.startswith("tf_"):
        tf_name = data.replace("tf_", "")
        symbol_name = context.user_data.get("selected_symbol", "EUR/USD OTC")

        back_keyboard = [
            [InlineKeyboardButton("🔄 تحليل مجدداً", callback_data=f"sym_{symbol_name}")],
            [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")],
        ]

        await query.message.edit_text("⏳ جاري جلب بيانات السوق الحقيقية وتحليلها...")
        result = get_signal(symbol_name, tf_name)

        if "error" in result:
            await query.message.edit_text(f"⚠️ {result['error']}", reply_markup=InlineKeyboardMarkup(back_keyboard))
            return

        disclaimer = (
            "\n\nℹ️ ملاحظة: هذا تحليل فني آلي وليس نصيحة استثمارية أو ضماناً للربح. "
            "الأسواق المالية والعملات الرقمية والخيارات الثنائية تحمل مخاطرة عالية."
        )
        result_text = (
            f"📊 نتيجة التحليل\n"
            f"─────────────────\n"
            f"{result.get('desc', '')}"
            f"{disclaimer}"
        )
        
        await query.message.edit_text(
            result_text, 
            reply_markup=InlineKeyboardMarkup(back_keyboard)
        )
        


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("cat_"):
        market_key = data.replace("cat_", "")
        # استخدام CATEGORIES مباشرة لأنها مخزنة كقوائم
        symbols = CATEGORIES.get(market_key, [])
        context.user_data["current_market"] = market_key

        keyboard = []
        for i in range(0, len(symbols), 2):
            row = [InlineKeyboardButton(symbols[i], callback_data=f"sym_{symbols[i]}")]
            if i + 1 < len(symbols):
                row.append(InlineKeyboardButton(symbols[i + 1], callback_data=f"sym_{symbols[i + 1]}"))
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        label = CATEGORY_LABELS.get(market_key, market_key)
        await query.message.edit_text(f"📁 {label}\nاختر الأصل:", reply_markup=reply_markup)

    elif data == "main_menu":
        await start(update, context)

    elif data.startswith("sym_"):
        symbol_name = data.replace("sym_", "")
        context.user_data["selected_symbol"] = symbol_name

        keyboard = []
        row = []
        for tf in TIMEFRAMES:
            row.append(InlineKeyboardButton(tf, callback_data=f"tf_{tf}"))
            if len(row) == 4:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        market_key = context.user_data.get("current_market", "forex")
        keyboard.append([InlineKeyboardButton("🔙 رجوع للقائمة", callback_data=f"cat_{market_key}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(f"⏱️ اختر الفريم الزمني لـ *{symbol_name}*:",
                                       reply_markup=reply_markup, parse_mode="Markdown")

    elif data.startswith("tf_"):
        tf_name = data.replace("tf_", "")
        symbol_name = context.user_data.get("selected_symbol", "EUR/USD")

        back_keyboard = [
            [InlineKeyboardButton("🔄 تحليل مجدداً", callback_data=f"sym_{symbol_name}")],
            [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")],
        ]

        await query.message.edit_text("⏳ جاري جلب بيانات السوق الحقيقية وتحليلها...")
        result = get_signal(symbol_name, tf_name)

        if "error" in result:
            await query.message.edit_text(f"⚠️ {result['error']}", reply_markup=InlineKeyboardMarkup(back_keyboard))
            return

        disclaimer = (
            "\n\nℹ️ ملاحظة: هذا تحليل فني آلي وليس نصيحة استثمارية أو ضماناً للربح. "
            "الأسواق المالية والعملات الرقمية والخيارات الثنائية تحمل مخاطرة عالية. "
            "اختبر الإشارات على حساب تجريبي قبل أي استخدام فعلي."
        )
        result_text = (
            f"📊 نتيجة التحليل\n"
            f"─────────────────\n"
            f"{result.get('desc', '')}"
            f"{disclaimer}"
        )
        
        await query.message.edit_text(
            result_text, 
            reply_markup=InlineKeyboardMarkup(back_keyboard)
        )


def main():
    TOKEN = os.environ.get("BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
    
         
    

    

    
    
    
    
    
    
    
    
    
            
    
    
    
    
    
        
