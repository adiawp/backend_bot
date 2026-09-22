# ☁️ Panduan Deployment Backend Bot Trading ke Google Cloud Platform (GCP)

Dokumen ini berisi panduan langkah demi langkah untuk melakukan deploy backend Python (`backend_bot`) ke Google Cloud Platform (GCP) agar bot dapat berjalan **24/7 di Cloud** dan diakses oleh **Aplikasi Android (`BottradingDashboard`)** dari mana saja via internet.

---

## 🛠️ Persiapan Awal
1. **Akun GCP**: Buat akun di [Google Cloud Console](https://console.cloud.google.com/).
2. **Google Cloud SDK (`gcloud` CLI)**: Download dan install [gcloud CLI](https://cloud.google.com/sdk/docs/install) di komputer Anda.
3. Login `gcloud` via terminal komputer:
   ```bash
   gcloud auth login
   gcloud config set project ID_PROJEK_GCP_ANDA
   ```

---

## 🚀 Opsi A: Deployment via Google Cloud Run (Serverless & HTTPS Otomatis) - *DIREKOMENDASIKAN*

Google Cloud Run sangat cocok karena otomatis menyediakan **URL HTTPS aman** (contoh: `https://bottrading-api-xxx.a.run.app`) yang langsung bisa diisikan ke **Settings IP di Aplikasi Android**.

### Langkah-langkah:
1. Buka terminal di folder `backend_bot`:
   ```bash
   cd C:\Users\Fadli\AndroidStudioProjects\BottradingDashboard\backend_bot
   ```

2. Aktifkan Service Cloud Build & Cloud Run di GCP:
   ```bash
   gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
   ```

3. Build Container & Deploy langsung ke Cloud Run:
   ```bash
   gcloud run deploy bottrading-api \
     --source . \
     --region asia-southeast1 \
     --allow-unauthenticated \
     --set-env-vars BYBIT_API_KEY="KEY_BYBIT_ANDA",BYBIT_API_SECRET="SECRET_BYBIT_ANDA",TESTNET="True"
   ```

4. Setelah proses deploy selesai, terminal akan menampilkan **Service URL**:
   ```text
   Service [bottrading-api] has been deployed and is available at:
   https://bottrading-api-12345678-as.a.run.app
   ```

5. **Masukkan URL tersebut ke Aplikasi Android**:
   * Buka aplikasi **BottradingDashboard** di HP Xiaomi Anda.
   * Ketuk ikon **Settings (Roda Gigi)** di pojok kanan atas.
   * Masukkan URL GCP tersebut: `https://bottrading-api-12345678-as.a.run.app`
   * Tekan **Simpan**. Selesai!

---

## 💻 Opsi B: Deployment via Google Compute Engine (Virtual Machine Always-On)

Jika Anda menginginkan server VM Ubuntu penuh yang selalu aktif dengan database SQLite persistent:

### Langkah-langkah:
1. **Buat Instance Compute Engine (VM)**:
   * Buka GCP Console > Compute Engine > VM instances > **Create Instance**.
   * Nama: `bot-trading-vm`
   * Region: `asia-southeast1 (Jakarta)` atau `asia-southeast2`
   * Machine type: `e2-micro` (Hemat biaya / Gratis Tier)
   * OS: `Ubuntu 22.04 LTS`
   * Firewall: Centang **Allow HTTP traffic** dan **Allow HTTPS traffic**.

2. **Buka Port 8000 pada Firewall GCP**:
   * Buka VPC Network > Firewall > Create Firewall Rule.
   * Target: All instances in the network.
   * Source IPv4 ranges: `0.0.0.0/0`
   * Protocols and ports: Specified protocols and ports > `tcp: 8000`.

3. **SSH ke VM Instance**:
   Jalankan di VM Ubuntu melalui browser/terminal SSH:
   ```bash
   sudo apt update && sudo apt install -y python3-pip python3-venv git
   git clone <URL_REPOSITORY_ANDA>
   cd backend_bot
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Jalankan Bot sebagai Systemd Service (Otomatis menyala jika VM reboot)**:
   Buat file service:
   ```bash
   sudo nano /etc/systemd/system/bottrading.service
   ```
   Isi file:
   ```ini
   [Unit]
   Description=Bybit Trading Bot FastAPI Service
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/backend_bot
   ExecStart=/home/ubuntu/backend_bot/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
   Aktifkan & Jalankan service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable bottrading
   sudo systemctl start bottrading
   ```

5. **Gunakan External IP VM pada Aplikasi Android**:
   * Ambil External IP dari GCP Console (misal `34.101.X.X`).
   * Masukkan di Settings Aplikasi Android: `http://34.101.X.X:8000`.

---

## 🔐 Keamanan Kredensial (API Key)
Selalu simpan `BYBIT_API_KEY` dan `BYBIT_API_SECRET` melalui **Environment Variables** di GCP, bukan di-hardcode pada file source code.
