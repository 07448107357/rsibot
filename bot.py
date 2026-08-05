import os
import telebot
from telebot import types
import pandas as pd
import yfinance as yf

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# قائمة الأزواج والرموز المربوطة بالسوق
PAIRS = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "AUD/USD": "AUDUSD=X",
    "USD/JPY": "USDJPY=X",
    "USD/CHF": "USDCHF=X",
    "USD/CAD": "USDCAD=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X",
    "Gold (XAU/USD)": "GC=F"
}

def get_real_rsi(ticker_symbol):
    try:
        data = yf.download(tickers=ticker_symbol, period="1d", interval="1m", progress=False)
        if len(data) < 15:
            return None
        
        close_prices = data['Close']
        if isinstance(close_prices, pd.DataFrame):
            close_prices = close_prices.iloc[:, 0]
            
        delta = close_prices.diff()
        gain = delta.clip(lower=0).rolling(window=14).mean()
        loss = (-delta.clip(upper=0)).rolling(window=14).mean()
        
        last_gain = gain.iloc[-1]
        last_loss = loss.iloc[-1]
        
        if pd.isna(last_gain) or pd.isna(last_loss) or (last_gain == 0 and last_loss == 0):
            return None
            
        if last_loss == 0:
            return 100.0
            
        rs = last_gain / last_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return float(rsi)
    except Exception as e:
        print(f"Error for {ticker_symbol}: {e}")
        return None

# بناء شبكة الأزرار
def build_pairs_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for pair_display in PAIRS.keys():
        # نرسل اسم الزوج في البيانات المخفية للزر (callback_data)
        btn = types.InlineKeyboardButton(text=pair_display, callback_data=f"get_{pair_display}")
        buttons.append(btn)
    markup.add(*buttons)
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = "📲 **اختر زوج العملات من القائمة أدناه للتحليل الفوري:**"
    bot.reply_to(message, welcome_text, reply_markup=build_pairs_keyboard(), parse_mode='Markdown')

# الاستجابة للضغط على أي زر عملة
@bot.callback_query_handler(func=lambda call: call.data.startswith('get_'))
def handle_pair_selection(call):
    pair_display = call.data.replace('get_', '')
    ticker_symbol = PAIRS.get(pair_display)
    
    # رسالة مؤقتة تشير لجاري التحليل
    bot.answer_callback_query(call.id, text=f"Creating signal for {pair_display}...")
    
    rsi_val = get_real_rsi(ticker_symbol)
    
    if rsi_val is None:
        msg = f"⚠️ **{pair_display}**\nعذراً، البيانات غير متوفرة حالياً لهذا الزوج."
    else:
        # تحديد حالة السوق بناءً على القيمة
        if rsi_val <= 40:
            status = "🟢 **BUY SIGNAL (CALL / UP)**\nمنطقة تشبع بيعي / صعود"
        elif rsi_val >= 60:
            status = "🔴 **SELL SIGNAL (PUT / DOWN)**\nمنطقة تشبع شرائي / هبوط"
        else:
            status = "⚪ **NEUTRAL (WAIT)**\nالسوق في مسار متوازن حالياً"
            
        msg = (
            f"📊 **Asset:** {pair_display}\n"
            f"📈 **RSI (1M):** {rsi_val:.1f}\n"
            f"⏱ **Duration:** 1 Minute\n\n"
            f"{status}"
        )
    
    # إرسال النتيجة مع إعادة إظهار قائمة العملات لسهولة الاختيار مجدداً
    bot.send_message(call.message.chat.id, msg, reply_markup=build_pairs_keyboard(), parse_mode='Markdown')

if __name__ == '__main__':
    print("Interactive Bot starting...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
    
    
    
    
    
    
