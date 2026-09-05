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

def analyze_market(df, pair_name, tf_name):
    import pandas as pd
    import numpy as np

    df = df.copy()

    # --- إصلاح مهم: التأكد من ترتيب البيانات تصاعدياً حسب الوقت ---
    # إذا كانت أحدث شمعة في أول الصفوف بدلاً من آخرها، فإن iloc[-1]
    # سيقرأ سعراً قديماً وليس السعر الحالي، وهذا سبب شائع لظهور
    # نفس التوصية (بيع فقط) بشكل متكرر.
    for time_col in ('time', 'timestamp', 'date', 'datetime'):
        if time_col in df.columns:
            df = df.sort_values(time_col).reset_index(drop=True)
            break

    closes = pd.to_numeric(df['close'], errors='coerce')
    if closes.isna().all():
        raise ValueError("عمود 'close' لا يحتوي على بيانات رقمية صالحة")

    current_price = float(closes.iloc[-1])

    # 1. RSI 14 و RSI 9
    delta = closes.diff()
    gain_14 = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss_14 = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs_14 = gain_14 / loss_14.replace(0, np.nan)
    rsi_14 = 100 - (100 / (1 + rs_14))
    current_rsi_14 = float(rsi_14.iloc[-1]) if not pd.isna(rsi_14.iloc[-1]) else 50.0

    gain_9 = delta.where(delta > 0, 0).rolling(window=9).mean()
    loss_9 = (-delta.where(delta < 0, 0)).rolling(window=9).mean()
    rs_9 = gain_9 / loss_9.replace(0, np.nan)
    rsi_9 = 100 - (100 / (1 + rs_9))
    current_rsi_9 = float(rsi_9.iloc[-1]) if not pd.isna(rsi_9.iloc[-1]) else 50.0

    # 2. EMA 14 + قياس ميل المتوسط (صاعد/هابط)
    ema_14 = closes.ewm(span=14, adjust=False).mean()
    current_ema = float(ema_14.iloc[-1])
    prev_ema = float(ema_14.iloc[-2]) if len(ema_14) > 1 else current_ema

    # 3. بولينجر بانز
    window = 20
    sma = closes.rolling(window=window).mean()
    std = closes.rolling(window=window).std()
    upper_band = sma + (std * 2)
    lower_band = sma - (std * 2)
    current_upper = float(upper_band.iloc[-1]) if not pd.isna(upper_band.iloc[-1]) else current_price
    current_lower = float(lower_band.iloc[-1]) if not pd.isna(lower_band.iloc[-1]) else current_price

    # --- 4. نظام تصويت متعدد العوامل بدل الاعتماد على مقارنة واحدة فقط ---
    # كل عامل يصوّت +1 (صعود) أو -1 (هبوط)، فيصبح الاتجاه النهائي
    # نتيجة توافق عدة مؤشرات، ما يمنع "التحيز" الدائم لجهة واحدة.
    score = 0

    # (أ) السعر مقابل EMA
    if current_price > current_ema:
        score += 1
    elif current_price < current_ema:
        score -= 1

    # (ب) ميل EMA نفسه (هل المتوسط صاعد أم هابط؟)
    if current_ema > prev_ema:
        score += 1
    elif current_ema < prev_ema:
        score -= 1

    # (ج) منطقة RSI14
    if current_rsi_14 > 55:
        score += 1
    elif current_rsi_14 < 45:
        score -= 1

    # (د) تقاطع RSI9 مع RSI14 (زخم قصير المدى)
    if current_rsi_9 > current_rsi_14:
        score += 1
    elif current_rsi_9 < current_rsi_14:
        score -= 1

    # (هـ) موقع السعر داخل نطاق بولينجر
    band_width = current_upper - current_lower
    if band_width > 0:
        position_in_band = (current_price - current_lower) / band_width
        if position_in_band > 0.5:
            score += 1
        elif position_in_band < 0.5:
            score -= 1

    # --- كسر التعادل: عند score == 0 لا نترك القرار معلقاً، بل نستخدم
    # فروقاً أدق (المسافة الفعلية بين السعر والـ EMA، ثم RSI9 كحكم أخير)
    # لإجبار القرار على CALL أو PUT دائماً ---
    if score == 0:
        if current_price != current_ema:
            score = 1 if current_price > current_ema else -1
        elif current_rsi_9 != 50.0:
            score = 1 if current_rsi_9 > 50.0 else -1
        else:
            score = 1  # تعادل تام نادر جداً: نميل افتراضياً لصالح CALL

    if score > 0:
        signal_type = "CALL"
        action_title = "🚀 **إشارة شراء / صعود (CALL)**"
        decision_text = f"القرار: دخول صفقة شراء (Call) — قوة الإشارة: {score}/5 مؤشرات صاعدة."
        trend_desc = "أغلب المؤشرات (الاتجاه، ميل EMA، RSI، بولينجر) تدعم الصعود."
    else:
        signal_type = "PUT"
        action_title = "📉 **إشارة بيع / هبوط (PUT)**"
        decision_text = f"القرار: دخول صفقة بيع (Put) — قوة الإشارة: {abs(score)}/5 مؤشرات هابطة."
        trend_desc = "أغلب المؤشرات (الاتجاه، ميل EMA، RSI، بولينجر) تدعم الهبوط."

    desc = (f"{action_title}\n"
            f"• الزوج: `{pair_name}` | الفريم: `{tf_name}`\n"
            f"• السعر الحالي: `{current_price:.4f}`\n"
            f"• 📈 مؤشر EMA (14): `{current_ema:.4f}`\n"
            f"• 📊 مؤشر RSI (14): `{current_rsi_14:.1f}`\n"
            f"• 📊 مؤشر RSI (9): `{current_rsi_9:.1f}`\n"
            f"• 🌐 الاتجاه الفني: {trend_desc}\n"
            f"• {decision_text}")

    return signal_type, desc



import pandas as pd
import yfinance as yf

# ==========================================
# 1. دالة جلب البيانات الأساسية
# ==========================================
def fetch_market_data(symbol: str, interval: str = "5m", limit: int = 200):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="5d", interval=interval, timeout=10)
        if df is None or df.empty:
            return None
        df = df.tail(limit).reset_index()
        df.columns = [str(col).lower() for col in df.columns]
        if 'close' not in df.columns:
            return None
        df['close'] = df['close'].astype(float)
        return df
    except Exception as e:
        print(f"خطأ في جلب البيانات لـ {symbol}: {e}")
        return None

# ==========================================
# 2. دوال حساب المؤشرات المالية
# ==========================================
def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_ema(df: pd.DataFrame, period: int) -> pd.Series:
    return df['close'].ewm(span=period, adjust=False).mean()

def build_recommendation(rsi: float, ema_fast: float, ema_slow: float) -> str:
    if rsi <= 30 and ema_fast > ema_slow:
        return "🟢 إشارة: شراء قوي (CALL / BUY)"
    elif rsi >= 70 and ema_fast < ema_slow:
        return "🔴 إشارة: بيع قوي (PUT / SELL)"
    elif rsi <= 35:
        return "🟢 إشارة: شراء (CALL / BUY)"
    elif rsi >= 65:
        return "🔴 إشارة: بيع (PUT / SELL)"
    return "⚪ إشارة: محايد / انتظار"
    


# تأكد من وجود هذه الدالة بالكامل في الكود لديك
def get_signal(name: str, timeframe: str = "5m") -> dict:
    try:
        raw_name = name.upper().replace("OTC", "").replace("/", "").replace("-", "").strip()
        clean_symbol = "".join(e for e in raw_name if e.isalnum())

        if clean_symbol in ["GOLD", "XAUUSD"]:
            symbol = "GC=F"
        elif clean_symbol in ["AAPL", "APPLE"]:
            symbol = "AAPL"
        else:
            if clean_symbol.endswith("X") and not clean_symbol.endswith("=X"):
                symbol = f"{clean_symbol[:-1]}=X"
            elif not clean_symbol.endswith("=X"):
                symbol = f"{clean_symbol}=X"
            else:
                symbol = clean_symbol

        df = fetch_market_data(symbol, timeframe, limit=200)

        if (df is None or df.empty) and not symbol.endswith("=X"):
            symbol = clean_symbol
            df = fetch_market_data(symbol, timeframe, limit=200)

        if df is None or df.empty or len(df) < 35:
            return {"error": f"بيانات غير كافية أو رمز غير صحيح ({name})."}

        rsi_series = calculate_rsi(df, period=14)
        ema_fast_series = calculate_ema(df, period=9)
        ema_slow_series = calculate_ema(df, period=21)

        current_rsi = round(float(rsi_series.iloc[-1]), 2)
        ema_fast = round(float(ema_fast_series.iloc[-1]), 4)
        ema_slow = round(float(ema_slow_series.iloc[-1]), 4)
        last_price = round(float(df["close"].iloc[-1]), 4)

        overall = build_recommendation(current_rsi, ema_fast, ema_slow)

        desc = (
            f"📈 الأصل: {symbol}\n"
            f"⏱️ الفريم: {timeframe}\n"
            f"💰 آخر سعر إغلاق: {last_price}\n\n"
            f"— RSI (14): {current_rsi}\n"
            f"— EMA9: {ema_fast} | EMA21: {ema_slow}\n\n"
            f"{overall}"
        )

        return {"desc": desc}
    except Exception as e:
        return {"error": f"حدث خطأ أثناء التحليل: {str(e)}"}
        

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
        symbol_name = context.user_data.get("selected_symbol", "#")

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
    
         
    

    

    
    
    
    
    
    
    
    
    
            
    
    
    
    
    
        
