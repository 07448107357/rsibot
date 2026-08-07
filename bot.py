import os
import time
import telebot
from telebot import types
import yfinance as yf
import pandas as pd

TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

PAIRS = {
    # --- أزواج العملات الرئيسية (Majors) ---
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "AUD/USD": "AUDUSD=X",
    "NZD/USD": "NZDUSD=X",
    "USD/JPY": "USDJPY=X",
    "USD/CHF": "USDCHF=X",
    "USD/CAD": "USDCAD=X",

    # --- أزواج اليورو (EUR Pairs) ---
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "EUR/CHF": "EURCHF=X",
    "EUR/CAD": "EURCAD=X",
    "EUR/AUD": "EURAUD=X",
    "EUR/NZD": "EURNZD=X",

    # --- أزواج الباوند (GBP Pairs) ---
    "GBP/JPY": "GBPJPY=X",
    "GBP/CHF": "GBPCHF=X",
    "GBP/CAD": "GBPCAD=X",
    "GBP/AUD": "GBPAUD=X",
    "GBP/NZD": "GBPNZD=X",

    # --- أزواج الين والفرنك والكرونا (Cross Pairs) ---
    "AUD/JPY": "AUDJPY=X",
    "AUD/CAD": "AUDCAD=X",
    "AUD/NZD": "AUDNZD=X",
    "AUD/CHF": "AUDCHF=X",
    "CAD/JPY": "CADJPY=X",
    "CAD/CHF": "CADCHF=X",
    "CHF/JPY": "CHFJPY=X",
    "NZD/JPY": "NZDJPY=X",
    "NZD/CAD": "NZDCAD=X",
    "NZD/CHF": "NZDCHF=X",

    # --- المعادن والسلع (Commodities) ---
    "Gold (XAU/USD)": "GC=F",
    "Silver (XAG/USD)": "SI=F",
    "Crude Oil (USOIL)": "CL=F",

    # --- الأسهم العالمية المتاحة في المنصة (Stocks) ---
    "Apple 🍎": "AAPL",
    "Amazon 📦": "AMZN",
    "McDonald's 🍔": "MCD",
    "Meta (Facebook) 🌐": "META",
    "Google 🔍": "GOOGL",
    "Tesla ⚡️": "TSLA",
    "Microsoft 💻": "MSFT",
    "Boeing ✈️": "BA",
    "Intel 💻": "INTC"
}

                # 1. حساب المؤشرات الإضافية
        


        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        # Stochastic Oscillator (14, 3, 3)
        low_min = df['Low'].rolling(window=14).min()
        high_max = df['High'].rolling(window=14).max()
        df['%K'] = 100 * ((df['Close'] - low_min) / (high_max - low_min))
        df['%D'] = df['%K'].rolling(window=3).mean()
        
        stoch_k = round(float(df['%K'].iloc[-1]), 2)
        stoch_d = round(float(df['%D'].iloc[-1]), 2)
        ema200 = float(df['EMA200'].iloc[-1])

        # 2. تحديد اتجاه السوق القوي (EMA 200 + SMA 20)
        if price > ema200 and price > sma:
            direction = "صاعد قوي ⬆️"
        elif price < ema200 and price < sma:
            direction = "هابط قوي ⬇️"
        else:
            direction = "عرضي / غير مستقر 🔄"
            
        

        # 3. شروط التوصية عالية الدقة (High Accuracy Strategy)
        # شراء: تريند صاعد + RSI في منطقة مناسبة + Stochastic يعطي تقاطع صاعد من الأسفل
        if "صاعد" in direction and rsi < 60 and stoch_k < 40 and stoch_k > stoch_d:
            signal = "🟢 STRONG BUY (CALL / UP) 🔥"
        
        # بيع: تريند هابط + RSI في منطقة مناسبة + Stochastic يعطي تقاطع هابط من الأعلى
        elif "هابط" in direction and rsi > 40 and stoch_k > 60 and stoch_k < stoch_d:
            signal = "🔴 STRONG SELL (PUT / DOWN) 🔥"
            
        else:
            signal = "⚪️ NEUTRAL (WAIT FOR SETUP)"

            
            
            
            
            
    
                



            





    
    
    
    
    
    
    
    
    
    
    
