# -*- coding: utf-8 -*-
# Binance USDT Perp Scanner – Render Enhanced Version (API4 FIX)
# By Kelly Juliana / GPT-5 Assistant
# Version: Render Full (API4 + Telegram notifications)

import ccxt
import pandas as pd
import numpy as np
import requests
from datetime import datetime

# ===== Telegram Configuration =====
TELEGRAM_TOKEN = "8331474411:AA6W5wl_4m7KuBUdQ8nNi8L1gntx0NN2RUw"
CHAT_ID = "1982879600"

# ===== Helper: Send Telegram Message =====
def send_telegram(msg: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": msg}
        requests.post(url, data=payload)
    except Exception as e:
        print(f"[ERROR] Telegram send failed: {e}")

# ===== Main Scan Function =====
def scan_once():
    print(f"\n[INFO {datetime.utcnow().strftime('%H:%M:%S')}] 🚀 Starting Binance scan...")
    send_telegram("🔍 Starting Binance scan on Render...")

    try:
        exchange = ccxt.binance({
            "enableRateLimit": True,
            "options": {"defaultType": "future"},
            "urls": {"api": {"public": "https://api4.binance.com"}}  # ✅ Mirror API to avoid regional block
        })
        markets = exchange.load_markets()
        pairs = [s for s in markets if s.endswith('/USDT') and 'PERP' in s]
        print(f"[INFO] ✅ Connected to Binance via api4. {len(pairs)} perpetual pairs detected.")
    except Exception as e:
        print(f"[ERROR] ❌ Binance connection failed: {e}")
        send_telegram(f"⚠️ Binance connection failed: {e}")
        return

    bullish, bearish = [], []
    count = 0

    for symbol in pairs:
        try:
            count += 1
            if count % 20 == 0:
                print(f"[INFO] Progress: {count}/{len(pairs)} pairs scanned...")

            ohlcv = exchange.fetch_ohlcv(symbol, "1h", limit=100)
            df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
            df['ema_fast'] = df['c'].ewm(span=12).mean()
            df['ema_slow'] = df['c'].ewm(span=26).mean()
            df['macd'] = df['ema_fast'] - df['ema_slow']
            df['signal'] = df['macd'].ewm(span=9).mean()

            macd_cross = df['macd'].iloc[-1] > df['signal'].iloc[-1]
            rsi = 100 - (100 / (1 + (df['c'].pct_change().clip(lower=0).mean() / abs(df['c'].pct_change().clip(upper=0).mean()))))

            if macd_cross and rsi > 55:
                bullish.append(symbol)
            elif not macd_cross and rsi < 45:
                bearish.append(symbol)

        except Exception as e:
            print(f"[WARN] {symbol} skipped: {e}")
            continue

    print(f"\n[INFO] Scan complete ✅")
    print(f"[INFO] Bullish signals: {len(bullish)} | Bearish signals: {len(bearish)}")
    send_telegram(f"✅ Scan complete.\nBullish: {len(bullish)} | Bearish: {len(bearish)}")

    if bullish:
        send_telegram("🚀 Bullish signals detected:\n" + "\n".join(bullish[:20]))
    if bearish:
        send_telegram("🔻 Bearish signals detected:\n" + "\n".join(bearish[:20]))

if __name__ == '__main__':
    print("[INFO] Running scan_once.py (Render environment, API4 mirror active)")
    try:
        scan_once()
        print("[INFO] Render execution finished successfully ✅")
    except Exception as e:
        print(f"[CRITICAL] Unhandled error: {e}")
        send_telegram(f"🚨 Critical bot error: {e}")
