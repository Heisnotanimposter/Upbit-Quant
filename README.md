# 🌌 UPbit-Quant: Advanced Quantitative Trading Platform (2026 Edition)

[![CI/CD Pipeline](https://github.com/your-username/UPbit-Quant/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/your-username/UPbit-Quant/actions)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/your-app)

A professional-grade quantitative trading platform for UPbit, modernized for 24/7 autonomous research and execution. This platform bridges the gap between high-frequency data ingestion, AI-driven strategy discovery, and strict algorithmic risk management.

---

## 🧭 Step-by-Step Setup Tutorial

Welcome to the UPbit-Quant ecosystem! Follow these steps to get full access to the AI-driven trading features.

### 1️⃣ Obtain Your API Keys

You need two sets of keys to unlock the platform's full potential:

#### 🇰🇷 UPbit Open API (Exchange Access)
*Used for fetching your real-time wallet balance and executing trades.*
1.  Log in to [UPbit (Korea)](https://upbit.com/service_center/open_api_guide).
2.  Go to **Service Center** > **Open API**.
3.  Click **Create Open API Key**.
4.  **CHECK** these permissions:
    *   `Asset Inquiry` (to see your holdings)
    *   `Order Placing` (to buy/sell)
    *   `Order Inquiry` (to check order status)
5.  **IP Address Registration (Mandatory)**: UPbit requires you to link your computer's public IP address for security. This allows the bot to trade ONLY from your trusted network.
6.  Copy your **Access Key** and **Secret Key**. *Warning: You will only see the Secret Key once!*

#### 🧠 OpenAI API (AI Strategy Intelligence)
*Used by the Strategy Agent to analyze market indicators and generate code.*
1.  Go to the [OpenAI Platform](https://platform.openai.com/api-keys).
2.  Create a new **Secret Key**.
3.  Ensure your account has a few dollars of credit for usage (the agent uses low-cost models by default).

---

### 2️⃣ Configure Your Environment

The platform uses **Streamlit Secrets** for safe credential management.

1.  In the project root directory, create a hidden folder named `.streamlit` (if it doesn't exist).
2.  Create a file named `secrets.toml` inside that folder.
3.  Paste your keys in the following format:

```toml
# .streamlit/secrets.toml
UPBIT_ACCESS_KEY = "PASTE_YOUR_UPBIT_ACCESS_KEY_HERE"
UPBIT_SECRET_KEY = "PASTE_YOUR_UPBIT_SECRET_KEY_HERE"
OPENAI_API_KEY = "PASTE_YOUR_OPENAI_API_KEY_HERE"
```

> [!IMPORTANT]
> **Never commit your `secrets.toml` to GitHub.** It is already included in the `.gitignore` to prevent accidental exposure of your funds.

---

### 3️⃣ Installation & Launch

Open your terminal (CMD or PowerShell on Windows, Terminal on Mac/Linux) and run:

```bash
# 1. Install all required modern libraries
pip install -r requirements.txt

# 2. Run the platform
streamlit run app.py
```

---

## 📈 Your First Research Session

Once the dashboard opens in your browser, follow this "Best Practice" flow:

1.  **System Health**: Check the `System Health` page. Green lights across "API Connectivity" and "Diagnostic Integrity" mean you are ready.
2.  **AI Strategy Generation**: Visit the `AI Strategy Agency` page. Input your goal (e.g., "Momentum trading on BTC during high volume") and let the LLM generate your indicators.
3.  **Backtesting Lab**: Test your new strategy! Set an **IS/OOS (In-Sample/Out-of-Sample)** split of 70/30. This ensures your strategy isn't just "lucky" on past data.
4.  **Stress Testing**: Before switching to Live Mode, run a **Black Swan Simulation** in the `Stress Tester` to see how your stop-loss reacts to a flash crash.
5.  **Live Trading (Paper Mode)**: Start the trading engine in **Paper Trading mode** first. This uses your real-time data but executes trades into a virtual wallet for 100% risk-free testing.

---

## 🏗️ Architecture Layout

```
UPbit-quant/
├── src/
│   ├── core/               # Critical system engines (Risk, OMS, Data)
│   ├── agents/             # AI Intelligence (LLM Strategy Agent)
│   └── utils/              # Calculation & Validation helpers
├── pages/                  # Interactive UI Dashboard Pages
├── tests/                  # 110+ Automated Reliability Tests
└── app.py                  # Main Entry Point
```

---

**⚠️ Disclaimer**: This software is for educational and professional quantitative research purposes. Trading cryptocurrencies involves extreme risk of capital loss. **Paper Trading mode is strictly recommended** for all new strategies.
