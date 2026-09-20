import sqlite3
import csv
import os

DB_NAME = "trading.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            side TEXT,
            qty REAL,
            entry_price REAL,
            stop_loss REAL,
            take_profit REAL,
            status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def log_trade(symbol, side, qty, entry_price, stop_loss, take_profit, status="OPEN"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO trades (symbol, side, qty, entry_price, stop_loss, take_profit, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (symbol, side, qty, entry_price, stop_loss, take_profit, status))
    conn.commit()
    conn.close()

def get_all_trades():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM trades ORDER BY timestamp DESC')

    # Format output agar mudah dibaca oleh API/Android
    columns = [col[0] for col in cursor.description]
    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    conn.close()
    return rows

def export_to_csv(filename="riwayat_trading.csv"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM trades ORDER BY timestamp DESC')
    rows = cursor.fetchall()

    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([i[0] for i in cursor.description]) # Header kolom
        writer.writerows(rows)
    conn.close()
    return filename