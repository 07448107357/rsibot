import os
import time
import telebot
import pandas as pd
import numpy as np


bot = telebot.TeleBot ('8920172447:AAFrn1H4vsSJj6FEK30lYbWp75mZ91sbTVM')


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
    welcome_text = (
        "🤖 **Welcome to RSI OTC Signals Bot**\n\n"
        "Bot is active and connected to the server successfully! 🚀\n"
        "Market analysis in progress. Signals will be sent automatically."
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

def generate_signal(chat_id, pair_name, price_list):
    rsi_val = calculate_rsi(price_list)
    
    # BUY Signal (Oversold)
    if rsi_val <= 30:
        msg = (
            f"🟢 **BUY SIGNAL (CALL / UP)**\n\n"
            f"📊 **Pair:** {pair_name}\n"
            f"📈 **RSI Indicator:** {rsi_val:.1f} (Oversold)\n"
            f"⏱️ **Duration:** 1 Minute\n"
            f"🎯 **Platform:** Pocket Option (OTC)"
        )
        bot.send_message(chat_id, msg, parse_mode='Markdown')
        
    # SELL Signal (Overbought)
    elif rsi_val >= 70:
        msg = (
            f"🔴 **SELL SIGNAL (PUT / DOWN)**\n\n"
            f"📊 **Pair:** {pair_name}\n"
            f"📉 **RSI Indicator:** {rsi_val:.1f} (Overbought)\n"
            f"⏱️ **Duration:** 1 Minute\n"
            f"🎯 **Platform:** Pocket Option (OTC)"
        )
        bot.send_message(chat_id, msg, parse_mode='Markdown')

if __name__ == '__main__':
    print("Bot started running on Render...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
pyTelegramBotAPI
pandas
numpy
