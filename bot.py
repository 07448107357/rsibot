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
        # --- نظام تصويت معدل لضمان مرونة الصعود والهبوط ---
    score = 0

    # (أ) السعر مقابل EMA (نعطيه وزناً أكبر قليلاً)
    if current_price >= current_ema:
        score += 1.5
    else:
        score -= 1

    # (ب) ميل EMA نفسه
    if current_ema >= prev_ema:
        score += 1
    else:
        score -= 1

    # (ج) منطقة RSI14 (جعلنا النطاق أوسع بقليل لصالح الشراء إذا لم يكن في تشبع بيعي تام)
    if current_rsi_14 >= 50:
        score += 1
    else:
        score -= 1

    # (د) تقاطع RSI9 مع RSI14
    if current_rsi_9 >= current_rsi_14:
        score += 1
    else:
        score -= 1

    # (هـ) موقع السعر داخل نطاق بولينجر
    band_width = current_upper - current_lower
    if band_width > 0:
        position_in_band = (current_price - current_lower) / band_width
        if position_in_band >= 0.45:  # خفضنا المعيار قليلاً لسهولة الحصول على شراء
            score += 1
        else:
            score -= 1

    # القرار النهائي بناءً على النتيجة المعدلة (أي قيمة أكبر من الصفر ستعطي شراء مباشرة)
    if score > 0:
        signal_type = "CALL"
        action_title = "🚀 **إشارة شراء / صعود (CALL)**"
        decision_text = f"القرار: دخول صفقة شراء (Call) — الزخم يدعم الصعود."
        trend_desc = "المؤشرات الفنية تميل لصالح الاتجاه الصاعد."
    elif score < 0:
        signal_type = "PUT"
        action_title = "📉 **إشارة بيع / هبوط (PUT)**"
        decision_text = f"القرار: دخول صفقة بيع (Put) — الزخم يدعم الهبوط."
        trend_desc = "المؤشرات الفنية تميل لصالح الاتجاه الهابط."
    else:
        signal_type = "WAIT"
        action_title = "⏸ **لا توجد إشارة واضحة (انتظار)**"
        decision_text = f"القرار: الانتظار — السوق في حالة تذبذب."
        trend_desc = "تعادل في القوى بين الصعود والهبوط."
        
    

# --- واجهة تليجرام ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for cat in CATEGORIES.keys():
        keyboard.append([InlineKeyboardButton(cat, callback_data=f"cat_{cat}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = "🤖 **مرحباً بك في بوت التحليل الفني المتقدم**\n\nاختر القسم المطلوب:"
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.edit_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("cat_"):
        cat_name = data.replace("cat_", "")
        pairs = CATEGORIES.get(cat_name, [])
        keyboard = []
        for i in range(0, len(pairs), 2):
            row = [InlineKeyboardButton(pairs[i], callback_data=f"pair_{pairs[i]}")]
            if i + 1 < len(pairs):
                row.append(InlineKeyboardButton(pairs[i+1], callback_data=f"pair_{pairs[i+1]}"))
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(f"📁 قسم: *{cat_name}*\nاختر الزوج:", reply_markup=reply_markup, parse_mode="Markdown")

    elif data == "main_menu":
        await start(update, context)

    elif data.startswith("pair_"):
        pair_name = data.replace("pair_", "")
        context.user_data['selected_pair'] = pair_name
        keyboard = []
        row = []
        for tf in TIMEFRAMES:
            row.append(InlineKeyboardButton(tf, callback_data=f"tf_{tf}"))
            if len(row) == 3:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🔙 رجوع للأزواج", callback_data="cat_💱 العملات (Forex)")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(f"⏱️ اختر الفريم الزمني للزوج: *{pair_name}*", reply_markup=reply_markup, parse_mode="Markdown")

    elif data.startswith("tf_"):
        tf_name = data.replace("tf_", "")
        pair_name = context.user_data.get('selected_pair', 'EUR/USD OTC')
            
        try:
            # --- إنشاء بيانات DataFrame للاختبار والتحليل ---
            import pandas as pd
            import numpy as np
                
            np.random.seed(42)
            close_prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
            df = pd.DataFrame({'close': close_prices})
                
            analysis_result = analyze_market(df, pair_name, tf_name)
        if analysis_result is not None and isinstance(analysis_result, tuple) and len(analysis_result) == 2:
         signal, desc = analysis_result
     else:
         signal, desc = "WAIT", "⚠️ عذراً، لم يُرجِع مؤشر التحليل أي بيانات لهذا الفريم."
            
            
                
            result_text = (f"📊 **نتيجة التحليل**\n"
                           f"─────────────────\n"
                           f"🔹 الزوج: `{pair_name}`\n"
                           f"⏰ الفريم: `{tf_name}`\n\n"
                           f"{desc}")
                
            keyboard = [
                [InlineKeyboardButton("🔄 تحليل مجدداً", callback_data=f"pair_{pair_name}")],
                [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.edit_text(result_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        except Exception as e:
            print(f"Error in timeframe handler: {e}")
            await query.message.edit_text(f"⚠️ حدث خطأ أثناء معالجة التحليل: {e}", parse_mode='Markdown')
            
                
    
def main():
    TOKEN = os.environ.get("BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    # إضافة المعالجات (Handlers)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is starting...")
    
    # التشغيل المباشر والمستقر
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
    
        
    
    
    

    
    
    
    
    
    
    
    
    
            
    
    
    
    
    
        
