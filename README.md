# UPbit Quantitative Trading Platform

[![CI/CD Pipeline](https://github.com/your-username/UPbit-Quant/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/your-username/UPbit-Quant/actions)
[![Code Coverage](https://codecov.io/gh/your-username/UPbit-Quant/branch/main/graph/badge.svg)](https://codecov.io/gh/your-username/UPbit-Quant)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A comprehensive quantitative trading platform for cryptocurrency markets featuring advanced machine learning models, reinforcement learning algorithms, and modern software engineering practices.

## 🚀 Features

- **Advanced Trading Algorithms**: Q-Learning, genetic algorithms, and neural networks
- **Real-time Data Processing**: Web crawlers for financial news and market data
- **Modern Architecture**: Clean code structure with proper error handling and logging
- **Comprehensive Testing**: Unit tests, integration tests, and performance benchmarks
- **Docker Support**: Containerized deployment with Docker and Docker Compose
- **CI/CD Pipeline**: Automated testing, building, and deployment
- **Web Interface**: Streamlit-based dashboard for interactive analysis
- **CLI Tools**: Command-line interface for training and testing models

## 📊 Screenshots

![TradePotential](https://github.com/Heisnotanimposter/Upbit-Quant/assets/97718938/50c561e0-b2b2-450d-b673-f325b2841742)
![GreedIndex](https://github.com/Heisnotanimposter/Upbit-Quant/assets/97718938/482ac860-9368-477c-9ce0-e93a134e5e0d)
![FearIndex](https://github.com/Heisnotanimposter/Upbit-Quant/assets/97718938/8c74ba2f-4ace-4628-9999-2a852931e0c5)
![coinnet](https://github.com/Heisnotanimposter/Upbit-Quant/assets/97718938/c939950f-83a2-44ee-bade-af48f78400bb)

## 🏗️ Architecture

```
upbit_quant/
├── core/                    # Core functionality
│   ├── config.py           # Configuration management
│   ├── logger.py           # Logging system
│   └── exceptions.py       # Custom exceptions
├── utils/                   # Utility modules
│   ├── validation.py       # Input validation
│   ├── decorators.py       # Useful decorators
│   └── helpers.py          # Helper functions
├── main/                    # Main application modules
│   ├── TradingEnvironment.py # Trading environment
│   └── Backtesting.py      # Backtesting framework
├── ticker/                  # Trading bot implementations
│   └── Trader1.py          # Q-Learning bot
├── crawler/                 # Data collection
├── gui/                     # User interfaces
└── tests/                   # Test suite
```

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- pip or conda
- Git

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/UPbit-Quant.git
   cd UPbit-Quant
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up configuration**
   ```bash
   cp config.env.example .env
   # Edit .env with your configuration
   ```

4. **Run tests**
   ```bash
   pytest tests/
   ```

### Docker Installation

1. **Using Docker Compose**
   ```bash
   docker-compose up -d
   ```

2. **Using Docker directly**
   ```bash
   docker build -t upbit-quant .
   docker run -p 8501:8501 upbit-quant
   ```

## 🚀 Usage

### Command Line Interface

```bash
# Train a trading bot
upbit-quant train --symbol BTC-KRW --episodes 1000

# Test a trained model
upbit-quant test --model-path models/bot.pkl --symbol BTC-KRW

# Start web interface
upbit-quant web --host 0.0.0.0 --port 8501

# Fetch market data
upbit-quant fetch-data --symbol BTC-KRW --days 30 --output data/btc_data.csv

# Display configuration
upbit-quant config-info
```

### Python API

```python
from upbit_quant.main.TradingEnvironment import TradingEnv
from upbit_quant.ticker.Trader1 import QLearningBot, QLearningConfig

# Create trading environment
prices = [100, 105, 110, 108, 112, 115, 113, 118, 120, 122]
env = TradingEnv(prices=prices, initial_balance=10000)

# Create Q-Learning bot
config = QLearningConfig(alpha=0.5, gamma=0.6, epsilon=0.1)
bot = QLearningBot(env.action_space, config)

# Train the bot
for episode in range(1000):
    bot.train_episode(env)

# Get performance metrics
performance = bot.get_performance_summary()
print(f"Performance: {performance}")
```

### Web Interface

Start the Streamlit web interface:

```bash
streamlit run GUI/PythonUI/QuantStreamlit.py
```

Then open your browser to `http://localhost:8501`

## 📈 Trading Strategies

### Q-Learning Bot

The Q-Learning bot uses reinforcement learning to learn optimal trading strategies:

- **State Space**: Balance, asset value, position size, current price
- **Action Space**: Hold, Buy, Sell with variable amounts
- **Reward Function**: Based on portfolio value changes
- **Exploration**: Epsilon-greedy policy with decay

### Genetic Algorithm

Optimizes trading parameters through evolutionary computation:

- **Population**: Set of trading strategies
- **Fitness**: Portfolio performance metrics
- **Selection**: Tournament selection
- **Crossover**: Parameter recombination
- **Mutation**: Random parameter changes

### Neural Networks

Deep learning models for price prediction and signal generation:

- **Architecture**: LSTM networks for time series
- **Features**: Technical indicators, market sentiment
- **Training**: Historical price data
- **Validation**: Walk-forward analysis

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=upbit_quant --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Exclude slow tests
```

## 📊 Performance Monitoring

The platform includes comprehensive performance monitoring:

- **Metrics**: Sharpe ratio, maximum drawdown, win rate
- **Logging**: Structured logging with different levels
- **Monitoring**: Real-time performance tracking
- **Alerts**: Email notifications for significant events

## 🔧 Configuration

Configuration is managed through environment variables and configuration files:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/upbit_quant

# Trading
DEFAULT_INITIAL_BALANCE=10000
MAX_POSITION_SIZE=1000
RISK_TOLERANCE=0.02

# API Keys
UPBIT_ACCESS_KEY=your_access_key
UPBIT_SECRET_KEY=your_secret_key
```

## 🚀 Deployment

### Production Deployment

1. **Set up environment**
   ```bash
   export DEBUG=False
   export LOG_LEVEL=INFO
   export DATABASE_URL=postgresql://...
   ```

2. **Run migrations**
   ```bash
   python manage.py migrate
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

### Cloud Deployment

The platform supports deployment on various cloud platforms:

- **AWS**: ECS, Lambda, EC2
- **Google Cloud**: Cloud Run, Compute Engine
- **Azure**: Container Instances, App Service

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Install development dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev]"
   ```
4. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```
5. **Make your changes and test**
   ```bash
   pytest
   black upbit_quant tests
   flake8 upbit_quant tests
   ```
6. **Commit your changes**
   ```bash
   git commit -m "Add amazing feature"
   ```
7. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```
8. **Create a Pull Request**

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Wiki](https://github.com/your-username/UPbit-Quant/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-username/UPbit-Quant/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/UPbit-Quant/discussions)
- **Email**: support@upbit-quant.com

## 🙏 Acknowledgments

- OpenAI for GPT models and research
- The Python community for excellent libraries
- Contributors and users of this project

## 📊 Roadmap

- [ ] Advanced ML models (Transformer, GAN)
- [ ] Multi-asset trading support
- [ ] Real-time trading execution
- [ ] Advanced risk management
- [ ] Mobile app
- [ ] API documentation
- [ ] Performance optimization
- [ ] Additional exchanges support

---

**⚠️ Disclaimer**: This software is for educational and research purposes only. Trading cryptocurrencies involves substantial risk of loss and is not suitable for all investors. Past performance does not guarantee future results.
