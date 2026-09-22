import os

# Config API Key & Secret Bybit
# Sistem akan mengutamakan Environment Variables dari Railway / GCP / Cloud
BYBIT_API_KEY = os.getenv("BYBIT_API_KEY", "MASUKKAN_BYBIT_API_KEY_ANDA")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET", "MASUKKAN_BYBIT_API_SECRET_ANDA")

# PENTING: Bybit punya 3 lingkungan server API yang TERPISAH TOTAL.
# API Key yang dibuat di satu lingkungan TIDAK BISA dipakai di lingkungan lain
# (akan selalu balas 401 Unauthorized walau key/secret-nya benar).
#
#   "demo"    -> Akun Demo Trading di bybit.com (toggle "Demo Trading" di web/app Bybit).
#                Server: api-demo.bybit.com
#   "testnet" -> Akun di testnet.bybit.com (situs terpisah, key dibuat di sana).
#                Server: api-testnet.bybit.com
#   "live"    -> Akun Bybit asli, uang sungguhan.
#                Server: api.bybit.com
#
# Kalau API Key kamu dibuat lewat bybit.com dengan badge "Demo Trading" (seperti
# di screenshot kamu), mode yang benar adalah "demo", BUKAN "testnet".
BYBIT_MODE = os.getenv("BYBIT_MODE", "demo").lower()
