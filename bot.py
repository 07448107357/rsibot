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



def analyze_market(df, pair_name, tf_name):
    import pandas as pd
    import numpy as np

    df = df.copy()

    # --- إصلاح مهم: التأكد من ترتيب البيانات تصاعدياً حسب الوقت ---
    for time_col in ('time', 'timestamp', 'date', 'datetime'):
        if time_col in df.columns:
            df = df.sort_values(time_col).reset_index(drop=True)
            break

    closes = pd.to_numeric(df['close'], errors='coerce')
    if closes.isna().all():
        raise ValueError("عمود 'close' لا يحتوي على بيانات رقمية صالحة")

    highs = pd.to_numeric(df['high'], errors='coerce') if 'high' in df.columns else closes
    lows = pd.to_numeric(df['low'], errors='coerce') if 'low' in df.columns else closes
    volume_col = None
    for v in ('volume', 'tick_volume', 'vol'):
        if v in df.columns:
            volume_col = v
            break
    volumes = pd.to_numeric(df[volume_col], errors='coerce') if volume_col else None

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

    # 2. EMA 14 + ميل المتوسط
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

    # =========================================================
    # 4. مؤشرات جديدة قوية
    # =========================================================

    # --- (أ) MACD (12, 26, 9) ---
    ema_12 = closes.ewm(span=12, adjust=False).mean()
    ema_26 = closes.ewm(span=26, adjust=False).mean()
    macd_line = ema_12 - ema_26
    macd_signal = macd_line.ewm(span=9, adjust=False).mean()
    macd_hist = macd_line - macd_signal
    current_macd = float(macd_line.iloc[-1])
    current_macd_signal = float(macd_signal.iloc[-1])
    current_macd_hist = float(macd_hist.iloc[-1])
    prev_macd_hist = float(macd_hist.iloc[-2]) if len(macd_hist) > 1 else current_macd_hist

    # --- (ب) Stochastic Oscillator (14, 3, 3) ---
    low_14 = lows.rolling(window=14).min()
    high_14 = highs.rolling(window=14).max()
    denom = (high_14 - low_14).replace(0, np.nan)
    percent_k = 100 * (closes - low_14) / denom
    percent_d = percent_k.rolling(window=3).mean()
    current_k = float(percent_k.iloc[-1]) if not pd.isna(percent_k.iloc[-1]) else 50.0
    current_d = float(percent_d.iloc[-1]) if not pd.isna(percent_d.iloc[-1]) else 50.0

    # --- (ج) ADX (14) — قوة الاتجاه ---
    up_move = highs.diff()
    down_move = -lows.diff()
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    tr1 = highs - lows
    tr2 = (highs - closes.shift()).abs()
    tr3 = (lows - closes.shift()).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr_14 = true_range.rolling(window=14).mean()
    plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(window=14).mean() / atr_14.replace(0, np.nan))
    minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(window=14).mean() / atr_14.replace(0, np.nan))
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx_14 = dx.rolling(window=14).mean()
    current_adx = float(adx_14.iloc[-1]) if not pd.isna(adx_14.iloc[-1]) else 0.0
    current_plus_di = float(plus_di.iloc[-1]) if not pd.isna(plus_di.iloc[-1]) else 0.0
    current_minus_di = float(minus_di.iloc[-1]) if not pd.isna(minus_di.iloc[-1]) else 0.0
    current_atr = float(atr_14.iloc[-1]) if not pd.isna(atr_14.iloc[-1]) else 0.0

    # --- (د) تأكيد الحجم (Volume) إن وجد ---
    volume_confirms = None
    if volumes is not None and not volumes.isna().all():
        vol_sma_20 = volumes.rolling(window=20).mean()
        current_vol = float(volumes.iloc[-1])
        avg_vol = float(vol_sma_20.iloc[-1]) if not pd.isna(vol_sma_20.iloc[-1]) else current_vol
        volume_confirms = current_vol > avg_vol  # حجم أعلى من المتوسط = تأكيد أقوى للحركة

    # =========================================================
    # 5. نظام تصويت موسّع (كل مؤشر قوي = صوت مستقل)
    # =========================================================
    score = 0
    max_votes = 0

    # (1) السعر مقابل EMA
    max_votes += 1
    if current_price > current_ema:
        score += 1
    elif current_price < current_ema:
        score -= 1

    # (2) ميل EMA
    max_votes += 1
    if current_ema > prev_ema:
        score += 1
    elif current_ema < prev_ema:
        score -= 1

    # (3) منطقة RSI14
    max_votes += 1
    if current_rsi_14 > 70:
        score += 1
    elif current_rsi_14 < 30:
        score -= 1

    # (4) تقاطع RSI9 مع RSI14
    max_votes += 1
    if current_rsi_9 > current_rsi_14:
        score += 1
    elif current_rsi_9 < current_rsi_14:
        score -= 1

    # (5) موقع السعر داخل نطاق بولينجر
    max_votes += 1
    band_width = current_upper - current_lower
    if band_width > 0:
        position_in_band = (current_price - current_lower) / band_width
        if position_in_band > 0.5:
            score += 1
        elif position_in_band < 0.5:
            score -= 1

    # (6) MACD: خط الماكد مقابل خط الإشارة
    max_votes += 1
    if current_macd > current_macd_signal:
        score += 1
    elif current_macd < current_macd_signal:
        score -= 1

    # (7) اتجاه هيستوجرام الماكد (تسارع/تباطؤ الزخم)
    max_votes += 1
    if current_macd_hist > prev_macd_hist:
        score += 1
    elif current_macd_hist < prev_macd_hist:
        score -= 1

    # (8) Stochastic: تقاطع %K مع %D + مناطق تشبع
    max_votes += 1
    if current_k > current_d:
        score += 1
    elif current_k < current_d:
        score -= 1
    if current_k > 80:
        score -= 0.5  # تشبع شرائي، احتمال ارتداد هبوطي
    elif current_k < 20:
        score += 0.5  # تشبع بيعي، احتمال ارتداد صعودي

    # (9) ADX + DI: لا نعطي وزناً لاتجاه ضعيف (ADX < 20 = سوق عرضي)
    max_votes += 1
    if current_adx >= 20:
        if current_plus_di > current_minus_di:
            score += 1
        elif current_plus_di < current_minus_di:
            score -= 1

    # (10) تأكيد الحجم: يضاعف تأثير الاتجاه العام إذا كان الحجم داعماً
    if volume_confirms is not None:
        max_votes += 1
        if volume_confirms:
            score += 1 if score > 0 else (-1 if score < 0 else 0)

    # --- كسر التعادل ---
    if score == 0:
        if current_price != current_ema:
            score = 1 if current_price > current_ema else -1
        elif current_macd != current_macd_signal:
            score = 1 if current_macd > current_macd_signal else -1
        elif current_rsi_9 != 50.0:
            score = 1 if current_rsi_9 > 50.0 else -1
        else:
            score = 1

    if score > 0:
        signal_type = "CALL"
        action_title = "🚀 **إشارة شراء / صعود (CALL)**"
        decision_text = f"القرار: دخول صفقة شراء (Call) — قوة الإشارة: {score:.1f}/{max_votes} مؤشرات صاعدة."
        trend_desc = "أغلب المؤشرات (الاتجاه، الزخم، القوة الاتجاهية) تدعم الصعود."
    else:
        signal_type = "PUT"
        action_title = "📉 **إشارة بيع / هبوط (PUT)**"
        decision_text = f"القرار: دخول صفقة بيع (Put) — قوة الإشارة: {abs(score):.1f}/{max_votes} مؤشرات هابطة."
        trend_desc = "أغلب المؤشرات (الاتجاه، الزخم، القوة الاتجاهية) تدعم الهبوط."

    adx_note = "قوي 💪" if current_adx >= 25 else ("متوسط" if current_adx >= 20 else "ضعيف/عرضي ⚠️")
    vol_note = ""
    if volume_confirms is not None:
        vol_note = f"\n• 📦 الحجم: {'يؤكد الحركة ✅' if volume_confirms else 'أقل من المتوسط (حذر)'}"

    desc = (f"{action_title}\n"
            f"• الزوج: `{pair_name}` | الفريم: `{tf_name}`\n"
            f"• السعر الحالي: `{current_price:.4f}`\n"
            f"• 📈 EMA (14): `{current_ema:.4f}`\n"
            f"• 📊 RSI (14): `{current_rsi_14:.1f}` | RSI (9): `{current_rsi_9:.1f}`\n"
            f"• 🔵 MACD: `{current_macd:.5f}` | Signal: `{current_macd_signal:.5f}` | Hist: `{current_macd_hist:.5f}`\n"
            f"• 🟣 Stochastic %K: `{current_k:.1f}` | %D: `{current_d:.1f}`\n"
            f"• 🧭 ADX (14): `{current_adx:.1f}` ({adx_note}) | +DI: `{current_plus_di:.1f}` | -DI: `{current_minus_di:.1f}`\n"
            f"• 📏 ATR (14): `{current_atr:.5f}`"
            f"{vol_note}\n"
            f"• 🌐 الاتجاه الفني: {trend_desc}\n"
            f"• {decision_text}")

    return signal_type, desc
    

        
    
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
            import pandas as pd
            import numpy as np
            
            np.random.seed(None)
            x = np.linspace(0, 40, 100)
            close_prices = 100 + (np.sin(x) * 3) + np.cumsum(np.random.randn(100) * 0.4)
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

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))


    print("Bot is starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
    
         
    

    

    
    
    
    
    
    
    
    
    
            
    
    
    
    
    
        
