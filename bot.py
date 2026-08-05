import os
import telebot
from telebot import types
import pandas as pd
import yfinance as yf

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

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

def analyze_market(ticker_symbol):
    try:
        data = yf.download(tickers=ticker_symbol, period="1d", interval="1m", progress=False)
        if len(data) < 20:
            return None, None
        
        close_prices = data['Close']
        if isinstance(close_prices, pd.DataFrame):
            close_prices = close_prices.iloc[:, 0]
            
        delta = close_prices.diff()
        gain = delta.clip(lower=0).rolling(window=14).mean()
        loss = (-delta.clip(upper=0)).rolling(window=14).mean()
        
        last_gain = gain.iloc[-1]
        last_loss = loss.iloc[-1]
        
        if pd.isna(last_gain) or pd.isna(last_loss) or (last_gain == 0 and last_loss == 0):
            return None, None
            
        rs = last_gain / (last_loss if last_loss != 0 else 1)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        
        ema_20 = close_prices.ewm(span=20, adjust=False).mean().iloc[-1]
        last_price = close_prices.iloc[-1]
        
        trend = "UP" if last_price >= ema_20 else "DOWN"
        
        return float(rsi), trend
    except Exception as e:
        print(f"Error analyzing {ticker_symbol}: {e}")
        return None, None

def build_pairs_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = [types.InlineKeyboardButton(text=pair, callback_data=f"get_{pair}") for pair in PAIRS.keys()]
    markup.add(*buttons)
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = "📲 **نظام الإشارات الفورية:**\nاختر زوج العملات للحصول على إشارة التداول:"
    bot.reply_to(message, welcome_text, reply_markup=build_pairs_keyboard(), parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data.startswith('get_'))
def handle_pair_selection(call):
    pair_display = call.data.replace('get_', '')
    ticker_symbol = PAIRS.get(pair_display)
    
    bot.answer_callback_query(call.id, text=f"Analyzing {pair_display}...")
    
    rsi_val, trend = analyze_market(ticker_symbol)
    
    if rsi_val is None:
        msg = f"⚠️ **{pair_display}**\nبيانات السوق غير متوفرة حالياً."
    else:
        if rsi_val <= 50:
            if rsi_val <= 35:
                signal_type = "🟢 **STRONG BUY SIGNAL (CALL / UP)**\n🎯 **السبب:** تشبع بيعي قوي (Oversold)"
            else:
                signal_type = "🟢 **BUY SIGNAL (CALL / UP)**\n🎯 **السبب:** المؤشر في النصف السفلي ويتجه للصعود"
        else:
            if rsi_val >= 65:
                signal_type = "🔴 **STRONG SELL SIGNAL (PUT / DOWN)**\n🎯 **السبب:** تشبع شرائي قوي (Overbought)"
            else:
                signal_type = "🔴 **SELL SIGNAL (PUT / DOWN)**\n🎯 **السبب:** المؤشر في النصف العلوي ويتجه للهبوط"
            
        msg = (
            f"📊 **Asset:** {pair_display}\n"
            f"📈 **RSI (1M):** {rsi_val:.1f}\n"
            f"📉 **Trend:** {trend}\n"
            f"⏱ **Duration:** 1 Minute\n\n"
            f"{signal_type}"
        )
    
    bot.send_message(call.message.chat.id, msg, reply_markup=build_pairs_keyboard(), parse_mode='Markdown')

if __name__ == '__main__':
    print("Starting bot safely...")
    # إزالة أي جلسة معلقة تمنع الاتصال وتسبب خطأ 409
    bot.remove_webhook()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
    
    
    
    
    
    
    
    
    
    
