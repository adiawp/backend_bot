import time
import threading
import pandas as pd
import numpy as np
from pybit.unified_trading import HTTP
from config import BYBIT_API_KEY as INITIAL_KEY, BYBIT_API_SECRET as INITIAL_SECRET, TESTNET as INITIAL_TESTNET
from database import log_trade

BYBIT_API_KEY = INITIAL_KEY
BYBIT_API_SECRET = INITIAL_SECRET
TESTNET = INITIAL_TESTNET

# Inisialisasi Client Bybit API
session = HTTP(
    testnet=TESTNET,
    api_key=BYBIT_API_KEY,
    api_secret=BYBIT_API_SECRET,
)

bot_is_running = False

def update_bybit_credentials(api_key: str, api_secret: str, testnet: bool = True):
    """Memperbarui kredensial API Bybit secara dinamis langsung dari Aplikasi Android."""
    global session, BYBIT_API_KEY, BYBIT_API_SECRET, TESTNET

    BYBIT_API_KEY = api_key.strip()
    BYBIT_API_SECRET = api_secret.strip()
    TESTNET = testnet

    try:
        session = HTTP(
            testnet=TESTNET,
            api_key=BYBIT_API_KEY,
            api_secret=BYBIT_API_SECRET,
        )
        mode_str = "Testnet (Demo)" if TESTNET else "Live Trading (Uang Asli)"
        print(f"🔑 API Key Bybit diperbarui! Mode: {mode_str}")
        return {"status": "SUCCESS", "message": f"API Key Bybit berhasil diperbarui! Mode: {mode_str}"}
    except Exception as e:
        return {"status": "ERROR", "message": f"Gagal memperbarui API Key: {e}"}

def get_bybit_config_status():
    """Mengembalikan status singkat konfigurasi API Key saat ini."""
    masked_key = BYBIT_API_KEY[:4] + "..." + BYBIT_API_KEY[-4:] if len(BYBIT_API_KEY) > 8 else "BELUM_DISET"
    return {
        "api_key_masked": masked_key,
        "testnet": TESTNET,
        "is_configured": len(BYBIT_API_KEY) > 8 and "MASUKKAN" not in BYBIT_API_KEY
    }

def get_bybit_wallet_balance():
    """Mengambil Saldo Dompet Bybit Unified Trading Account (USDT Balance, Equity)."""
    try:
        if len(BYBIT_API_KEY) > 8 and "MASUKKAN" not in BYBIT_API_KEY:
            response = session.get_wallet_balance(accountType="UNIFIED", coin="USDT")
            if 'result' in response and 'list' in response['result'] and len(response['result']['list']) > 0:
                item = response['result']['list'][0]
                total_equity = float(item.get('totalEquity', 0.0))
                total_available = float(item.get('totalAvailableBalance', 0.0))

                coin_list = item.get('coin', [])
                wallet_balance = total_equity
                if len(coin_list) > 0:
                    wallet_balance = float(coin_list[0].get('walletBalance', total_equity))

                return {
                    "status": "SUCCESS",
                    "usdt_balance": round(wallet_balance, 2),
                    "total_equity": round(total_equity, 2),
                    "total_available": round(total_available, 2)
                }
    except Exception as e:
        print(f"Error fetching wallet balance: {e}")

    return {
        "status": "NOT_CONFIGURED" if len(BYBIT_API_KEY) <= 8 or "MASUKKAN" in BYBIT_API_KEY else "ERROR",
        "usdt_balance": 0.0,
        "total_equity": 0.0,
        "total_available": 0.0
    }

def get_historical_data(symbol="BTCUSDT", interval="15", limit=100):
    """Mengambil data Candlestick (Kline) dari Bybit Futures API."""
    try:
        response = session.get_kline(
            category="linear", # Futures Perpetual
            symbol=symbol,
            interval=interval,
            limit=limit
        )
        data = response['result']['list']
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)

        df = df.iloc[::-1].reset_index(drop=True)
        return df
    except Exception as e:
        print(f"Error fetching kline data: {e}")
        return None

def calculate_indicators(df):
    if df is None or len(df) < 50:
        return df

    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['close'].ewm(span=200, adjust=False).mean()

    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    df['RSI_14'] = 100 - (100 / (1 + rs))

    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD_line'] = ema12 - ema26
    df['MACD_signal'] = df['MACD_line'].ewm(span=9, adjust=False).mean()
    df['MACD_hist'] = df['MACD_line'] - df['MACD_signal']

    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift(1)).abs()
    low_close = (df['low'] - df['close'].shift(1)).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR_14'] = true_range.rolling(window=14).mean()

    up_move = df['high'] - df['high'].shift(1)
    down_move = df['low'].shift(1) - df['low']
    pos_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    neg_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    tr_smooth = true_range.rolling(window=14).mean()
    pos_di = 100 * (pd.Series(pos_dm).rolling(window=14).mean() / (tr_smooth + 1e-10))
    neg_di = 100 * (pd.Series(neg_dm).rolling(window=14).mean() / (tr_smooth + 1e-10))
    dx = 100 * ((pos_di - neg_di).abs() / (pos_di + neg_di + 1e-10))
    df['ADX_14'] = dx.rolling(window=14).mean()

    sma20 = df['close'].rolling(window=20).mean()
    std20 = df['close'].rolling(window=20).std()
    df['BB_middle'] = sma20
    df['BB_upper'] = sma20 + (std20 * 2)
    df['BB_lower'] = sma20 - (std20 * 2)

    return df

def get_bybit_crypto_metrics(symbol="BTCUSDT"):
    funding_rate = 0.0
    open_interest = 0.0
    try:
        tickers = session.get_tickers(category="linear", symbol=symbol)
        if 'result' in tickers and 'list' in tickers['result'] and len(tickers['result']['list']) > 0:
            item = tickers['result']['list'][0]
            funding_rate = float(item.get('fundingRate', 0.0))
            open_interest = float(item.get('openInterest', 0.0))
    except Exception as e:
        print(f"Error fetching crypto metrics: {e}")

    return {
        "funding_rate": funding_rate,
        "open_interest": open_interest
    }

def get_market_analysis(symbol="BTCUSDT"):
    df = get_historical_data(symbol, interval="15", limit=100)
    if df is None:
        return {"status": "Error fetching market data"}

    df = calculate_indicators(df)
    last_row = df.iloc[-1]
    metrics = get_bybit_crypto_metrics(symbol)

    return {
        "symbol": symbol,
        "current_price": round(float(last_row['close']), 2),
        "rsi_14": round(float(last_row.get('RSI_14', 0.0)), 2),
        "ema_50": round(float(last_row.get('EMA_50', 0.0)), 2),
        "ema_200": round(float(last_row.get('EMA_200', 0.0)), 2),
        "macd_line": round(float(last_row.get('MACD_line', 0.0)), 2),
        "macd_signal": round(float(last_row.get('MACD_signal', 0.0)), 2),
        "macd_hist": round(float(last_row.get('MACD_hist', 0.0)), 2),
        "atr_14": round(float(last_row.get('ATR_14', 0.0)), 2),
        "adx_14": round(float(last_row.get('ADX_14', 0.0)), 2),
        "bb_upper": round(float(last_row.get('BB_upper', 0.0)), 2),
        "bb_middle": round(float(last_row.get('BB_middle', 0.0)), 2),
        "bb_lower": round(float(last_row.get('BB_lower', 0.0)), 2),
        "funding_rate": metrics["funding_rate"],
        "open_interest": metrics["open_interest"]
    }

def analyze_and_trade():
    global bot_is_running
    symbol = "BTCUSDT"

    print("🤖 Bot Trading Aktif! Menganalisa Market (Sistem Turtle Traders & Multi-Indikator)...")

    while bot_is_running:
        try:
            df = get_historical_data(symbol, interval="15", limit=100)
            if df is not None and len(df) >= 50:
                df = calculate_indicators(df)
                curr = df.iloc[-1]
                prev = df.iloc[-2]

                current_price = curr['close']
                ema_50 = curr['EMA_50']
                ema_200 = curr['EMA_200']
                rsi = curr['RSI_14']
                atr = curr['ATR_14']
                adx = curr['ADX_14']
                bb_upper = curr['BB_upper']
                bb_lower = curr['BB_lower']

                metrics = get_bybit_crypto_metrics(symbol)
                funding_rate = metrics['funding_rate']

                if pd.isna(ema_50) or pd.isna(ema_200) or pd.isna(atr):
                    time.sleep(15)
                    continue

                sl_distance = 2.0 * atr if not pd.isna(atr) else (current_price * 0.01)
                tp_distance = 2.0 * sl_distance
                qty = 0.001

                is_golden_cross = (ema_50 > ema_200) and (prev['EMA_50'] <= prev['EMA_200'])
                is_bb_breakout_up = (current_price > bb_upper)
                is_strong_trend = (adx > 20) if not pd.isna(adx) else True

                if (is_golden_cross or is_bb_breakout_up) and is_strong_trend and rsi < 70 and funding_rate < 0.0005:
                    sl_price = round(current_price - sl_distance, 2)
                    tp_price = round(current_price + tp_distance, 2)

                    print(f"🟢 Sinyal LONG (BUY) Terdeteksi! Harga: ${current_price}, SL: ${sl_price}, TP: ${tp_price}")

                    if len(BYBIT_API_KEY) > 8 and "MASUKKAN" not in BYBIT_API_KEY:
                        try:
                            session.place_order(category="linear", symbol=symbol, side="Buy", orderType="Market", qty=qty, stopLoss=sl_price, takeProfit=tp_price)
                            print("✅ Order Buy berhasil dipasang di Bybit!")
                        except Exception as err:
                            print(f"Error order Bybit: {err}")

                    log_trade(symbol, "Buy", qty, current_price, sl_price, tp_price, "OPEN")
                    time.sleep(60 * 15)

                is_death_cross = (ema_50 < ema_200) and (prev['EMA_50'] >= prev['EMA_200'])
                is_bb_breakout_down = (current_price < bb_lower)

                if (is_death_cross or is_bb_breakout_down) and is_strong_trend and rsi > 30:
                    sl_price = round(current_price + sl_distance, 2)
                    tp_price = round(current_price - tp_distance, 2)

                    print(f"🔴 Sinyal SHORT (SELL) Terdeteksi! Harga: ${current_price}, SL: ${sl_price}, TP: ${tp_price}")

                    if len(BYBIT_API_KEY) > 8 and "MASUKKAN" not in BYBIT_API_KEY:
                        try:
                            session.place_order(category="linear", symbol=symbol, side="Sell", orderType="Market", qty=qty, stopLoss=sl_price, takeProfit=tp_price)
                            print("✅ Order Sell berhasil dipasang di Bybit!")
                        except Exception as err:
                            print(f"Error order Bybit: {err}")

                    log_trade(symbol, "Sell", qty, current_price, sl_price, tp_price, "OPEN")
                    time.sleep(60 * 15)

        except Exception as e:
            print(f"Error pada loop trading: {e}")

        time.sleep(15)

def start_bot():
    global bot_is_running
    if not bot_is_running:
        bot_is_running = True
        threading.Thread(target=analyze_and_trade, daemon=True).start()

def stop_bot():
    global bot_is_running
    bot_is_running = False

def get_status():
    return "RUNNING" if bot_is_running else "STOPPED"
