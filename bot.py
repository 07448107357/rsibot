import os
import time
import threading
import telebot
import numpy as np
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
        if len(data) < 15:
            return None
        
        close_prices = data['Close'].values
        deltas = np.diff(close_prices)
        
        seed = deltas[:14]
        up = seed[seed >= 0].sum() / 14
        down = -seed[seed < 0].sum() / 14
        
        if down == 0:
            return 100
            
        rs = up / down
        rsi = 100. - 100. / (1. + rs)
        return float(rsi)
    except Exception as e:
        print(f"Error fetching data for {ticker_symbol}: {e}")
        return None

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_chats.add(message.chat.id)
    welcome_text = (
        "🤖 **Welcome to Real-Time RSI Signals Bot**\n\n"
        "✅ Connected to Live Market Data (Yahoo Finance)\n"
        "⚡ Scanning pairs for real RSI oversold (<30) & overbought (>70) conditions..."
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

def check_and_send_signals():
    while True:
        time.sleep(60) 
        for pair_display, pair_ticker in PAIRS.items():
            rsi_val = get_real_rsi(pair_ticker)
            
            if rsi_val is None:
                continue
                
            
            for cid in list(user_chats):
                if rsi_val <= 30:
                    msg = (
                        f"🟢 **REAL BUY SIGNAL (CALL / UP)**\n\n"
                        f"📊 **Pair:** {pair_display}\n"
                        f"📈 **RSI (1M):** {rsi_val:.1f} (Oversold)\n"
                        f"⏱ **Duration:** 1 Minute\n"
                        f"🌐 **Data:** Real-Time Market"
                    )
                    bot.send_message(cid, msg, parse_mode='Markdown')
                elif rsi_val >= 70:
                    msg = (
                        f"🔴 **REAL SELL SIGNAL (PUT / DOWN)**\n\n"
                        f"📊 **Pair:** {pair_display}\n"
                        f"📉 **RSI (1M):** {rsi_val:.1f} (Overbought)\n"
                        f"⏱ **Duration:** 1 Minute\n"
                        f"🌐 **Data:** Real-Time Market"
                    )
                    bot.send_message(cid, msg, parse_mode='Markdown')

if __name__ == '__main__':
    print("Bot with real market data started...")
    threading.Thread(target=check_and_send_signals, daemon=True).start()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
    
