from fastapi import FastAPI
from fastapi.responses import FileResponse
import database
import bot_logic
import os

app = FastAPI(title="Bybit Auto Trading Bot API")

@app.on_event("startup")
def startup_event():
    # Buat tabel database jika belum ada saat server menyala
    database.init_db()
    print("Database SQLite siap digunakan.")

@app.get("/")
def read_root():
    return {"message": "Server Bot Trading Aktif", "status": bot_logic.get_status()}

@app.post("/bot/start")
def start_trading_bot():
    if bot_logic.get_status() == "RUNNING":
        return {"message": "Bot sudah berjalan!"}
    bot_logic.start_bot()
    return {"message": "Bot berhasil dijalankan."}

@app.post("/bot/stop")
def stop_trading_bot():
    bot_logic.stop_bot()
    return {"message": "Bot berhasil dimatikan."}

@app.get("/bot/status")
def get_bot_status():
    return {"status": bot_logic.get_status()}

@app.get("/bot/indicators")
def get_market_indicators(symbol: str = "BTCUSDT"):
    # Endpoint untuk mengambil data analisis indikator teknikal & metrik Kripto
    return bot_logic.get_market_analysis(symbol)

@app.get("/bot/trades")
def get_trade_history():
    # Mengambil riwayat trading untuk ditampilkan di Dashboard HP Android
    trades = database.get_all_trades()
    return {"total_trades": len(trades), "trades": trades}

@app.get("/bot/export")
def export_trades_to_excel():
    # Meng-generate file CSV dari SQLite dan mengirimkannya ke klien (Android)
    filename = database.export_to_csv()
    file_path = os.path.join(os.getcwd(), filename)
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='text/csv'
    )

if __name__ == "__main__":
    import uvicorn
    # Jalankan server API (Mendukung port dari GCP)
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
