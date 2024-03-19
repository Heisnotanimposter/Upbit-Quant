import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.title('Quant Python Streamlit Example')

# Let's create a DataFrame with random data representing the "Fear Index" and "Greed Index"
date_range = pd.date_range(start='01-01-2019', end='12-31-2021', freq='B')
fear_index = np.random.randint(low=0, high=100, size=len(date_range))
greed_index = np.random.randint(low=0, high=100, size=len(date_range))

df = pd.DataFrame({'Fear Index': fear_index, 'Greed Index': greed_index}, index=date_range)

# Add sliders to adjust the thresholds for the Trade Potential calculation
fear_threshold = st.sidebar.slider('Fear Threshold', 0.0, 1.0, 0.7)
greed_threshold = st.sidebar.slider('Greed Threshold', 0.0, 1.0, 0.7)

# Recalculate the trade potential based on the new thresholds
trade_potential = np.where((greed_index / (greed_index + fear_index)) > greed_threshold, -1,
                           np.where((fear_index / (greed_index + fear_index)) > fear_threshold, 1, 0))
df['Trade Potential'] = trade_potential

st.write(df)

# Plot the Fear Index data
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(df.index, df['Fear Index'],
label='Fear Index', color='red')
ax.fill_between(df.index, df['Fear Index'], color='red', alpha=0.1)
ax.set_title('Stock Market Fear Index Over Time')
ax.set_xlabel('Date')
ax.set_ylabel('Fear Index')
ax.legend()
ax.grid(True)
st.pyplot(fig)

# Plot the Greed Index data
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(df.index, df['Greed Index'], label='Greed Index', color='blue')
ax.fill_between(df.index, df['Greed Index'], color='blue', alpha=0.1)
ax.set_title('Stock Market Greed Index Over Time')
ax.set_xlabel('Date')
ax.set_ylabel('Greed Index')
ax.legend()
ax.grid(True)
st.pyplot(fig)

# Plot the Trade Potential data
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(df.index, df['Trade Potential'], label='Trade Potential', color='green')
ax.fill_between(df.index, df['Trade Potential'], color='green', alpha=0.1)
ax.set_title('Stock Market Trade Potential Over Time')
ax.set_xlabel('Date')
ax.set_ylabel('Trade Potential')
ax.legend()
ax.grid(True)
st.pyplot(fig)

# Now can view streamlit app in browser, type this on terminal
# streamlit run /Users/'SeungwonLee'/'...'/streamlittest/QuantStreamlit.py
