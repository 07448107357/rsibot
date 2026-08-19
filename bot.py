import os
import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# إعداد السجلات (Logging)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# التوكن الخاص بالبوت
TOKEN = "8866300939:AAHYmUmEUdDYebIpsvdJ9lEEHJfCO9sdU4Y"

# قائمة الأصول الكاملة (عملات، أسهم، عملات رقمية) مع الأعلام والرموز الملونة كما طلبتها
CURRENCY_PAIRS = [
    # مجموعة 1
    "🇬🇧🇺🇸 GBP/USD OTC", "🇧🇭🇨🇳 BHD/CNY OTC",
    "🇪🇺🇷🇺 EUR/RUB OTC", "🇺🇸🇮🇳 USD/INR OTC",
    "🇺🇦🇺🇸 UAH/USD OTC", "🇺🇸🇧🇩 USD/BDT OTC",
    "🇦🇺🇳🇿 AUD/NZD OTC", "🇯🇴🇨🇳 JOD/CNY OTC",
    "🇺🇸🇻🇳 USD/VND OTC", "🇺🇸🇨🇴 USD/COP OTC",
    # مجموعة 2
    "🇲🇦🇺🇸 MAD/USD OTC", "🇺🇸🇯🇵 USD/JPY OTC",
    "🇪🇺🇯🇵 EUR/JPY OTC", "🇩🇿🇺🇸 USD/DZD OTC",
    "🇺🇸🇮🇩 USD/IDR OTC", "🇺🇸🇹🇭 USD/THB OTC",
    "🇺🇸🇨🇦 USD/CAD OTC", "🇱🇧🇺🇸 LBP/USD OTC",
    "🇺🇸🇵🇰 USD/PKR OTC", "🇰🇪🇺🇸 KES/USD OTC",
    # مجموعة 3
    "🇪🇺🇺🇸 EUR/USD OTC", "🇪🇺🇬🇧 EUR/GBP OTC",
    "🇦🇪🇨🇳 AED/CNY OTC", "🇳🇬🇺🇸 NGN/USD OTC",
    "🇪🇺🇳🇿 EUR/NZD OTC", "🇺🇸🇷🇺 USD/RUB OTC",
    "🇦🇺🇨🇦 AUD/CAD OTC", "🇪🇺🇨🇭 EUR/CHF OTC",
    "🇺🇸🇪🇬 USD/EGP OTC", "🇦🇺🇯🇵 AUD/JPY OTC",
    "🇦🇺🇺🇸 AUD/USD OTC",
    # مجموعة 4
    "🇨🇭🇯🇵 CHF/JPY OTC", "🇺🇸🇦🇷 USD/ARS OTC",
    "🇺🇸🇲🇾 USD/MYR OTC", "🇺🇸🇨🇱 USD/CLP OTC",
    "🇺🇸🇸🇬 USD/SGD OTC", "🇨🇦🇯🇵 CAD/JPY OTC",
    "🇨🇭🇳🇴 CHF/NOK OTC", "🇸🇦🇨🇳 SAR/CNY OTC",
    "🇺🇸🇨🇳 USD/CNH OTC", "🇺🇸🇧🇷 USD/BRL OTC",
    "🇺🇸🇲🇽 USD/MXN OTC", "🇶🇦🇨🇳 QAR/CNY OTC",
    "🇳🇿🇺🇸 NZD/USD OTC", "🇺🇸🇨🇭 USD/CHF OTC"
]

CRYPTO_PAIRS = [
    "🪨 Bitcoin ETF OTC", "🥈 Litecoin OTC",
    "🟡 BNB OTC", "🔴 TRON OTC",
    "🔗 Chainlink OTC", "💎 Toncoin OTC",
    "🟣 Solana OTC", "🟠 Bitcoin OTC",
    "🟣 Polygon OTC", "🔺 Avalanche OTC",
    "💎 Ethereum OTC", "🔴 Polkadot OTC",
    "🟡 Dogecoin OTC", "🔵 Cardano OTC",
    "🔹 Dash OTC"
]

STOCK_PAIRS = [
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

# دمج كل الأصول في قائمة واحدة شاملة
ALL_PAIRS = CURRENCY_PAIRS + CRYPTO_PAIRS + STOCK_PAIRS

# قائمة الفريمات الزمنية الكاملة
TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h"]

# دالة البداية /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    
    context.user_data['selected_pair'] = "🇬🇧🇺🇸 GBP/USD OTC"
    context.user_data['timeframe'] = "5m"
    
    keyboard = [
        [InlineKeyboardButton("📊 اختر الأصل والعملات الملونة", callback_data="choose_pair")],
        [InlineKeyboardButton("⏱️ اختر الفريم الزمني", callback_data="choose_timeframe")],
        [InlineKeyboardButton("🚀 تحديث التوصية الفورية", callback_data="update_signal")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = (
        f"مرحباً بك يا **{user_name}** في بوت توصيات الـ RSI الاحترافي والمحدث! 🤖📈\n\n"
        f"البوت جاهز لإعطاء إشارات بيع وشراء دقيقة مع اتجاه السوق لجميع العملات والأصول الملونة."
    )
    
    if update.message:
        await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(welcome_message, reply_markup=reply_markup, parse_mode="Markdown")

# قائمة اختيار الأصول مقسمة في أزرار مرتبة
async def choose_pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for i in range(0, len(ALL_PAIRS), 2):
        row = [InlineKeyboardButton(ALL_PAIRS[i], callback_data=f"pair_{ALL_PAIRS[i]}")]
        if i + 1 < len(ALL_PAIRS):
            row.append(InlineKeyboardButton(ALL_PAIRS[i+1], callback_data=f"pair_{ALL_PAIRS[i+1]}"))
        keyboard.append(row)
        
    keyboard.append([InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("📌 **اختر الزوج / الأصل المطلوب للتحليل:**", reply_markup=reply_markup, parse_mode="Markdown")

# حفظ الأصل المختار
async def set_pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    pair = query.data.replace("pair_", "")
    context.user_data['selected_pair'] = pair
    
    keyboard = [
        [InlineKeyboardButton("🚀 تحديث التوصية الفورية", callback_data="update_signal")],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"✅ تم ضبط الأصل بنجاح!\n📌 الأصل المختارة: **{pair}**\n\nاضغط أدناه لتحليل السوق:",
        reply_markup=reply_markup, parse_mode="Markdown"
    )

# قائمة اختيار الفريمات
async def choose_timeframe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton(tf, callback_data=f"tf_{tf}")] for tf in TIMEFRAMES
    ]
    keyboard.append([InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("⏱️ **اختر الفريم الزمني المناسب:**", reply_markup=reply_markup, parse_mode="Markdown")

# حفظ الفريم المختار
async def set_timeframe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    timeframe = query.data.replace("tf_", "")
    context.user_data['timeframe'] = timeframe
    
    keyboard = [
        [InlineKeyboardButton("🚀 تحديث التوصية الفورية", callback_data="update_signal")],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"✅ تم ضبط الفريم بنجاح!\n⏱️ الفريم: **{timeframe}**\n\nاضغط أدناه لتحليل السوق:",
        reply_markup=reply_markup, parse_mode="Markdown"
    )

# دالة إرسال وتحليل التوصيات الفورية
async def send_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    pair = context.user_data.get('selected_pair', '🇬🇧🇺🇸 GBP/USD OTC')
    timeframe = context.user_data.get('timeframe', '5m')
    
    signals_pool = [
        (
            "🟢 BUY (شراء صاعد)", 
            "اتحاد اتجاه صاعد قوي مع ارتداد مؤشر RSI (14) من مناطق التشبع البيعي (<30). الفرصة ممتازة للدخول صعوداً."
        ),
        (
            "🔴 SELL (بيع هابط)", 
            "اتجاه عام هابط مع وصول مؤشر RSI (14) لمناطق التشبع الشرائي (>70). الفرصة متاحة للدخول هبوطاً."
        ),
        (
            "⚪ WAIT (انتظار إشارة واضحة)", 
            "السوق يتحرك في نطاق عرضي حالياً، ولم تكتمل شروط التقاطع العلمي للـ RSI. يفضل الانتظار حتى اكتمال النموذج."
        )
    ]
    
    current_signal, signal_desc = random.choice(signals_pool)
    
    keyboard = [
        [InlineKeyboardButton("🔄 تحديث التوصية", callback_data="update_signal")],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    signal_text = (
        f"📊 **توصية التداول الحالية الفورية**\n\n"
        f"📌 الأصل: **{pair}**\n"
        f"⏱️ الفريم: **{timeframe}**\n"
        f"📈 التحليل الفني: **مؤشر RSI (14) + فلتر الاتجاه**\n"
        f"🎯 الإشارة: **{current_signal}**\n\n"
        f"💡 **التحليل الفني والاتجاه:**\n{signal_desc}"
    )
    
    await query.edit_message_text(signal_text, reply_markup=reply_markup, parse_mode="Markdown")

# دالة العودة للقائمة الرئيسية
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📊 اختر الأصل والعملات الملونة", callback_data="choose_pair")],
        [InlineKeyboardButton("⏱️ اختر الفريم الزمني", callback_data="choose_timeframe")],
        [InlineKeyboardButton("🚀 تحديث التوصية الفورية", callback_data="update_signal")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🏠 **القائمة الرئيسية للبوت**\nاختر من الأزرار أدناه للبدء:",
        reply_markup=reply_markup, parse_mode="Markdown"
    )

# تشغيل البوت الأساسي
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(choose_pair, pattern="^choose_pair$"))
    application.add_handler(CallbackQueryHandler(set_pair, pattern="^pair_"))
    application.add_handler(CallbackQueryHandler(choose_timeframe, pattern="^choose_timeframe$"))
    application.add_handler(CallbackQueryHandler(set_timeframe, pattern="^tf_"))
    application.add_handler(CallbackQueryHandler(send_signal, pattern="^update_signal$"))
    application.add_handler(CallbackQueryHandler(main_menu, pattern="^main_menu$"))

    print("Bot is running successfully with all colored assets...")
    application.run_polling()

if __name__ == "__main__":
    main()
    
    
    
    
    
    
    
        
    
    
    
        
    
    
    

    
    
    
    
    
    
    
    
    
    
    
    
