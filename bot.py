import os
import time
import threading
import telebot
import pandas as pd
import yfinance as yf

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

user_chats = set()

PAIRS = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "AUD/USD": "AUDUSD=X",
    "USD/JPY": "USDJPY=X"
}

def get_real_rsi(ticker_symbol):
    try:
        data = yf.download(tickers=ticker_symbol, period="1d", interval="1m", progress=False)
        if len(data) < 20:
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

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_chats.add(message.chat.id)
    welcome_text = (
        "🤖 **Welcome to Real-Time RSI Signals Bot**\n\n"
        "✅ Connected to Live Market Data\n"
        "⚡ Validated RSI calculation active (BUY <= 35 | SELL >= 65)..."
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

def check_and_send_signals():
    while True:
        time.sleep(60)
        for pair_display, pair_ticker in PAIRS.items():
            rsi_val = get_real_rsi(pair_ticker)
            
            # تجاهل القيم المعدومة 0.0 أو الخاطئة
            if rsi_val is None or rsi_val <= 0.0 or rsi_val >= 100.0:
                continue
                
            for cid in list(user_chats):
                # إشارات الشراء للـ RSI المنخفض
                if rsi_val <= 35:
                    msg = (
                        f"🟢 **REAL BUY SIGNAL (CALL / UP)**\n\n"
                        f"📊 **Pair:** {pair_display}\n"
                        f"📈 **RSI (1M):** {rsi_val:.1f} (Oversold)\n"
                        f"⏱ **Duration:** 1 Minute\n"
                        f"🌐 **Data:** Real-Time Market"
                    )
                    bot.send_message(cid, msg, parse_mode='Markdown')
                # إشارات البيع للـ RSI المرتفع
                elif rsi_val >= 65:
                    msg = (
                        f"🔴 **REAL SELL SIGNAL (PUT / DOWN)**\n\n"
                        f"📊 **Pair:** {pair_display}\n"
                        f"📉 **RSI (1M):** {rsi_val:.1f} (Overbought)\n"
                        f"⏱ **Duration:** 1 Minute\n"
                        f"🌐 **Data:** Real-Time Market"
                    )
                    bot.send_message(cid, msg, parse_mode='Markdown')

if __name__ == '__main__':
    print("Bot starting with validated RSI algorithm...")
    threading.Thread(target=check_and_send_signals, daemon=True).start()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
    
    
    
    
    
