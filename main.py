from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
import database
import bot_logic
import os

app = FastAPI(title="Bybit Auto Trading Bot API")

class BybitConfigRequest(BaseModel):
    api_key: str
    api_secret: str
    testnet: bool = True

@app.on_event("startup")
def startup_event():
    database.init_db()
    print("Database SQLite siap digunakan.")

@app.get("/")
def read_root():
    return {"message": "Server Bot Trading Aktif", "status": bot_logic.get_status()}

@app.post("/bot/start")
@app.post("/bot/start/")
def start_trading_bot():
    if bot_logic.get_status() == "RUNNING":
        return {"message": "Bot sudah berjalan!"}
    bot_logic.start_bot()
    return {"message": "Bot berhasil dijalankan."}

@app.post("/bot/stop")
@app.post("/bot/stop/")
def stop_trading_bot():
    bot_logic.stop_bot()
    return {"message": "Bot berhasil dimatikan."}

@app.get("/bot/status")
@app.get("/bot/status/")
def get_bot_status():
    return {"status": bot_logic.get_status()}

@app.post("/bot/config")
@app.post("/bot/config/")
def update_bot_config(config: BybitConfigRequest):
    return bot_logic.update_bybit_credentials(config.api_key, config.api_secret, config.testnet)

@app.get("/bot/config")
@app.get("/bot/config/")
def get_bot_config():
    return bot_logic.get_bybit_config_status()

@app.get("/bot/indicators")
@app.get("/bot/indicators/")
def get_market_indicators(symbol: str = "BTCUSDT"):
    return bot_logic.get_market_analysis(symbol)

@app.get("/bot/trades")
@app.get("/bot/trades/")
def get_trade_history():
    trades = database.get_all_trades()
    return {"total_trades": len(trades), "trades": trades}

@app.get("/bot/export")
@app.get("/bot/export/")
def export_trades_to_excel():
    filename = database.export_to_csv()
    file_path = os.path.join(os.getcwd(), filename)
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='text/csv'
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
