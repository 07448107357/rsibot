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

    # التأكد من وجود أسعار الإغلاق
    closes = df['close']

    # 1. حساب مؤشر القوة النسبية RSI (فترة 14)
    delta = closes.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi_series = 100 - (100 / (1 + rs))
    current_rsi = rsi_series.iloc[-1]
    if pd.isna(current_rsi):
        current_rsi = 50.0

    # 2. حساب مؤشر بولينجر بانز (Bollinger Bands - فترة 20 والانحراف 2)
    window = 20
    sma = closes.rolling(window=window).mean()
    std = closes.rolling(window=window).std()
    upper_band = sma + (std * 2)
    lower_band = sma - (std * 2)
    
    current_price = closes.iloc[-1]
    current_upper = upper_band.iloc[-1]
    current_lower = lower_band.iloc[-1]
    current_sma = sma.iloc[-1]

    if pd.isna(current_upper):
        current_upper = current_price * 1.01
        current_lower = current_price * 0.99
        current_sma = current_price

    # 3. منطق إعطاء التوصية بناءً على المؤشرات مجتمعة
    signal = "WAIT"
    if current_price <= current_lower or current_rsi < 30:
        signal = "CALL"
        desc = (f"📈 **إشارة شراء / صعود (CALL)**\n"
                f"• المؤشرات: السعر لامس الخط السفلي للبولينجر أو RSI متدنٍ جداً.\n"
                f"• مؤشر RSI: `{current_rsi:.1f}`\n"
                f"• الحالة: فرصة محتملة للصعود.")
    elif current_price >= current_upper or current_rsi > 70:
        signal = "PUT"
        desc = (f"📉 **إشارة بيع / هبوط (PUT)**\n"
                f"• المؤشرات: السعر لامس الخط العلوي للبولينجر أو RSI مرتفع جداً.\n"
                f"• مؤشر RSI: `{current_rsi:.1f}`\n"
                f"• الحالة: فرصة محتملة للهبوط.")
    else:
        desc = (f"⚖️ **إشارة تداول جانبية**\n"
                f"• مؤشر RSI: `{current_rsi:.1f}`\n"
                f"• الحالة: السعر داخل حدود بولينجر بانز وفي منتصف القناة، يفضل الانتظار حتى يلامس الأطراف.")

    return signal, desc
    
        

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
            
            # --- إنشاء بيانات DataFrame افتراضية أو حقيقية للتحليل لكي يعمل الفريم ---
        import pandas as pd
        import numpy as np
            
            # توليد أسعار وهمية مؤقتة للاختبار الفوري لحين ربطها بمصدر بيانات حقيقي
        np.random.seed(42)
        close_prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
        df = pd.DataFrame({'close': close_prices})
            # -------------------------------------------------------------------
            
        signal, desc = analyze_market(df, pair_name, tf_name)
            
        result_text = f"📊 **نتيجة التحليل**\n" \
                      f"─────────────────\n" \
                      f"🔹 الزوج: `{pair_name}`\n" \
                      f"⏰ الفريم: `{tf_name}`\n\n" \
                      f"{desc}"
            
        keyboard = [
            [InlineKeyboardButton("🔄 تحليل مجدداً", callback_data=f"pair_{pair_name}")],
            [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(result_text, reply_markup=reply_markup, parse_mode='Markdown')
                
    
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
    
        
    
    
    

    
    
    
    
    
    
    
    
    
            
    
    
    
    
    
        
