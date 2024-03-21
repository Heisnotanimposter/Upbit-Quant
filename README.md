##Upbit-Quant : Crypto Analysis and Trading Bots


Introduction
This repository is dedicated to the development and testing of automated trading strategies for cryptocurrency markets. It features a collection of tools ranging from web crawlers for financial data acquisition to advanced machine learning models and genetic algorithms for market analysis and prediction.

Directory Structure
Crawler: Contains web crawlers such as BBCFinancialCrawler and NaverFinancialCrawler for collecting financial news data.
GUI: User interface components for interactive analysis (if applicable).
RLtest: Reinforcement learning models for developing trading strategies.
Ticker: Scripts for fetching and analyzing ticker information for various cryptocurrencies.
main: Core application codebase.
oracleDB: Database scripts and schemas for storing and managing financial data.
Data Collection
The Crawler directory includes scripts for fetching real-time financial news from sources like BBC and Naver. These scripts are built with robust error handling and are designed to extract relevant financial news that can impact cryptocurrency markets.

Machine Learning Models
In the RLtest directory, we test various reinforcement learning models to develop and refine trading strategies. The reinforcement learning environment is simulated with historical price data, allowing for extensive testing before deployment.

Ticker Analysis
The Ticker directory includes tools for real-time analysis of cryptocurrency prices. It uses data from .csv files like krw_btc_candlesticks.csv to analyze market trends and provide insights into potential trades.

Genetic Algorithms
Our genetic algorithm implementations are used to optimize trading strategies by simulating the evolution of trading parameters over time, leading to more refined and potentially profitable strategies.

Database
oracleDB contains all necessary SQL scripts for setting up the database that supports this project. It stores both raw and processed financial data, serving as the backbone for analysis tasks.

Usage
To get started, clone the repository and install the required dependencies:

bash
Copy code
git clone [repository link]
cd [repository name]
pip install -r requirements.txt
Then follow the instructions in the respective directories to run individual components.

Contribution
Contributions are welcome! Please read the contribution guidelines in CONTRIBUTING.md before submitting pull requests.

License
This project is licensed under the MIT License.

Contact
For any queries or collaborations, please open an issue in this repository or contact us directly at [contact information].
