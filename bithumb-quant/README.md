# ⚡ Bithumb Quant Auto-Trading Engine (24/7 Cloud + Google AI Studio)

A production-grade, fully autonomous quantitative cryptocurrency auto-trading system for the **Bithumb KRW Market**, featuring **Google AI Studio (Gemini 2.5 Flash)** market regime analysis, **$0/month cloud infrastructure strategy**, **2-way mobile Telegram control**, and **crash-resilient self-healing architecture**.

---

## 🌟 Key Features

1. **24/7 Cloud Operation with Google AI Studio**:
   - Integrates `google-genai` SDK with Gemini 2.5 Flash for market regime classification (`BULL`, `BEAR`, `CHOPPY`, `HIGH_RISK`).
   - Dynamically scales position allocation and halts trading during extreme market risk.
   - Generates daily Telegram portfolio performance briefings.

2. **$0 / Month Minimalist Maintenance Strategy**:
   - Optimized to run 100% within **GCP Always Free Tier (`e2-micro`)** or **Oracle Cloud Free Tier**.
   - Includes 2GB automated Swap allocation to prevent out-of-memory errors on 1GB RAM cloud servers.
   - Uses embedded SQLite with Write-Ahead Logging (WAL) for persistent state (no cloud database fees).

3. **Zero Local Interference (Eternal Cloud Run)**:
   - Systemd auto-restart daemon (`Restart=always`) and Docker Compose containerization.
   - Handles Bithumb exchange maintenance windows (502/503/504 errors) using exponential backoff retry.
   - NTP system time sync for Bithumb JWT Nonce authentication.

4. **Multi-Layer Risk Management**:
   - **Larry Williams Volatility Breakout + EMA Trend Filter + RSI Guard**.
   - **Emergency Daily Drawdown Circuit Breaker**: Auto-liquidates positions into KRW and pauses trading if 24h portfolio drawdown hits the threshold limit (default 5%).
   - Trailing Stop Loss & Hard Stop Loss.

5. **2-Way Telegram Mobile Cockpit**:
   - **Real-time Push Alerts**: BUY/SELL execution notifications, stop-loss triggers, daily PnL summary.
   - **Interactive Commands**: `/status`, `/balance`, `/pause`, `/resume`, `/closeall`.

---

## 🏗️ Architecture

```
bithumb-quant/
├── config/
│   ├── config.py             # Config parser & validator
│   └── settings.yaml         # Strategy, risk, and target symbols
├── src/
│   ├── api/
│   │   ├── bithumb_client.py # Bithumb v2 REST API (JWT auth & backoff retry)
│   │   └── gemini_advisor.py # Google AI Studio integration (Gemini 2.5 Flash)
│   ├── core/
│   │   ├── engine.py         # 24/7 Master Event Loop
│   │   ├── risk_manager.py   # Circuit breaker & position sizer
│   │   └── state_db.py       # SQLite WAL database manager
│   ├── strategies/
│   │   └── quant_strategy.py # Volatility Breakout + EMA + RSI strategy
│   └── utils/
│       └── telegram_bot.py   # Telegram push alerts & interactive commands
├── deploy/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── bithumb-quant.service
│   └── setup_gcp_vm.sh       # 1-Click GCP/OCI server bootstrap script
├── main.py                   # Application entry point
├── requirements.txt
└── .env.example
```

---

## 🚀 Quick Start (Local Setup & Paper Trading)

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/your-repo/bithumb-quant.git
cd bithumb-quant

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` with your API keys:
- `BITHUMB_ACCESS_KEY` & `BITHUMB_SECRET_KEY` (Get from Bithumb > API Management. **Grant ONLY Order and Query permissions**).
- `GEMINI_API_KEY` (Get free key from [Google AI Studio](https://aistudio.google.com/)).
- `TELEGRAM_BOT_TOKEN` & `TELEGRAM_CHAT_ID` (Create via @BotFather on Telegram).
- Keep `DRY_RUN=true` for paper trading mode.

### 3. Run Engine in Paper Trading Mode
```bash
python main.py
```

---

## ☁️ $0/Month Cloud Deployment Guide (GCP Always Free VM)

### Step 1: Create a Free GCP Compute Engine Instance
1. Go to Google Cloud Console > Compute Engine > VM Instances.
2. Select Region: `us-central1`, `us-west1`, or `us-east1` (Always Free Tier eligible).
3. Machine Configuration: **`e2-micro`** (1 vCPU, 1 GB RAM).
4. Boot Disk: **Ubuntu 22.04 LTS** (Standard Persistent Disk, 30 GB).

### Step 2: Run 1-Click Bootstrap Script
SSH into your GCP VM and execute:
```bash
git clone https://github.com/your-repo/bithumb-quant.git /opt/bithumb-quant
cd /opt/bithumb-quant
chmod +x deploy/setup_gcp_vm.sh
./deploy/setup_gcp_vm.sh
```

### Step 3: Set `.env` & Start Systemd Daemon
```bash
cd /opt/bithumb-quant
cp .env.example .env
nano .env  # Enter your actual Bithumb, Gemini, and Telegram API keys

# Start 24/7 Background Daemon
sudo systemctl start bithumb-quant

# Check Status & Real-time Logs
sudo systemctl status bithumb-quant
sudo journalctl -u bithumb-quant -f
```

---

## 📱 Mobile Telegram Commands

Send any of the following commands to your Telegram Bot:

- `/status` — View bot uptime, mode, active AI regime, and current holdings.
- `/balance` — View total KRW portfolio equity and available cash.
- `/pause` — Temporarily pause order generation.
- `/resume` — Resume automatic trading.
- `/closeall` — Emergency market sell all active coin holdings into KRW.

---

## ⚙️ Strategy Configuration (`config/settings.yaml`)

```yaml
symbols:
  - "BTC_KRW"
  - "ETH_KRW"
  - "XRP_KRW"
  - "SOL_KRW"

strategy:
  k_noise_ratio: 0.5            # Range multiplier k for target price
  ema_fast_period: 5             # Fast EMA
  ema_slow_period: 20            # Slow EMA
  rsi_max_buy: 70                # RSI overbought guard

risk:
  max_portfolio_allocation_pct: 20.0  # Max KRW allocation per coin
  default_stop_loss_pct: 3.0          # Hard stop loss %
  trailing_stop_activation_pct: 4.0   # Trailing stop activation trigger
  trailing_stop_distance_pct: 2.0     # Trailing stop distance
  daily_max_drawdown_pct: 5.0         # Circuit Breaker limit
```

---

## 🔒 Security Best Practices

- **API Permissions**: Never enable `Withdrawal` permissions on your Bithumb API key. Enable only `Order` and `Query`.
- **IP Whitelisting**: Set your cloud server's static IP address in Bithumb API IP restrictions.
- **Environment Safety**: Ensure `.env` is listed in `.gitignore` and never committed to version control.
