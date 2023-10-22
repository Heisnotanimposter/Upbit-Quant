import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import numpy as np
import yfinance as yf

# Define the top 10 virtual coins
top_coins = ['BTC', 'ETH', 'ADA', 'BNB', 'XRP', 'SOL', 'DOT', 'DOGE', 'USDT', 'AVAX']

# Streamlit UI
st.title('Crypto Price Forecasting')

option = st.selectbox('Select a cryptocurrency', top_coins)

if option:
    start_date = '2021-01-01'
    end_date = '2023-08-20'
    horizon_range = range(1, 13)

    coin_data = yf.download(f'{option}-USD', start=start_date, end=end_date)
    coin_monthly = coin_data['Adj Close'].resample('M').last().reset_index()
    coin_monthly['Month'] = coin_monthly['Date'].dt.month
    coin_monthly['Year'] = coin_monthly['Date'].dt.year

    st.write("### Historical Data")
    st.write(coin_monthly)

    # Linear Regression Forecast
    def linear_regression_forecast(coin_monthly, horizon):
        X = coin_monthly[['Month', 'Year']]
        y = coin_monthly['Adj Close']
        model = LinearRegression()
        model.fit(X, y)

        next_month = coin_monthly['Month'].iloc[-1] + horizon
        next_year = coin_monthly['Year'].iloc[-1]
        if next_month > 12:
            next_month -= 12
            next_year += 1

        next_price = model.predict([[next_month, next_year]])
        return next_price[0]

    st.write("### Linear Regression Forecast")
    st.write("Select a horizon for Linear Regression forecast:")
    horizon = st.slider("Horizon (in months)", 1, 12, 1)
    forecast_price = linear_regression_forecast(coin_monthly, horizon)
    st.write(f"Predicted price after {horizon} months: {forecast_price:.2f} USD")

    # Polynomial Regression Forecast
    def polynomial_regression_forecast(coin_monthly, horizon, degree=2):
        X = coin_monthly[['Month', 'Year']]
        y = coin_monthly['Adj Close']

        polynomial_features = PolynomialFeatures(degree=degree)
        X_poly = polynomial_features.fit_transform(X)

        model = LinearRegression()
        model.fit(X_poly, y)

        next_month = coin_monthly['Month'].iloc[-1] + horizon
        next_year = coin_monthly['Year'].iloc[-1]
        if next_month > 12:
            next_month -= 12
            next_year += 1

        next_price = model.predict(polynomial_features.transform([[next_month, next_year]]))
        return next_price[0]

    st.write("### Polynomial Regression Forecast")
    st.write("Select a horizon for Polynomial Regression forecast:")
    horizon_poly = st.slider("Horizon (in months)", 1, 12, 1)
    degree = st.slider("Degree of polynomial", 1, 10, 2)
    forecast_price_poly = polynomial_regression_forecast(coin_monthly, horizon_poly, degree)
    st.write(f"Predicted price after {horizon_poly} months using Polynomial Regression: {forecast_price_poly:.2f} USD")

    # Plotting
    st.write("### Historical and Forecasted Prices")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(coin_monthly['Date'], coin_monthly['Adj Close'], label='Historical', color='black')
    ax.set_title(f'{option} Price Over Time')
    ax.set_xlabel('Date')
    ax.set_ylabel('Price')
    ax.legend()
    ax.grid(True)

    forecast_dates = [coin_monthly['Date'].iloc[-1] + pd.DateOffset(months=horizon) for horizon in horizon_range]
    forecast_prices = [linear_regression_forecast(coin_monthly, h) for h in horizon_range]
    ax.plot(forecast_dates, forecast_prices, label=f'Linear Regression Forecast ({horizon_range[-1]} months)', linestyle='dashed')

    forecast_dates_poly = [coin_monthly['Date'].iloc[-1] + pd.DateOffset(months=horizon_poly) for horizon_poly in horizon_range]
    forecast_prices_poly = [polynomial_regression_forecast(coin_monthly, h, degree) for h in horizon_range]
    ax.plot(forecast_dates_poly, forecast_prices_poly, label=f'Polynomial Regression Forecast ({horizon_range[-1]} months, degree={degree})', linestyle='dashed')

    st.pyplot(fig)
