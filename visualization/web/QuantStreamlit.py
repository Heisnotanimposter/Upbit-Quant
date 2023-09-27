import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.title('Stock Market Analysis')

# Create a DataFrame with random data representing the "Fear Index" and "Greed Index"
date_range = pd.date_range(start='01-01-2019', end='12-31-2021', freq='B')
fear_index = np.random.randint(low=0, high=100, size=len(date_range))
greed_index = np.random.randint(low=0, high=100, size=len(date_range))

df = pd.DataFrame({'Date': date_range, 'Fear Index': fear_index, 'Greed Index': greed_index})

# Sidebar sliders for adjusting thresholds
st.sidebar.header('Threshold Settings')
fear_threshold = st.sidebar.slider('Fear Threshold', 0.0, 1.0, 0.7)
greed_threshold = st.sidebar.slider('Greed Threshold', 0.0, 1.0, 0.7)

# Calculate Trade Potential based on user-defined thresholds
trade_potential = np.where((greed_index / (greed_index + fear_index)) > greed_threshold, -1,
                           np.where((fear_index / (greed_index + fear_index)) > fear_threshold, 1, 0))
df['Trade Potential'] = trade_potential

# Display the DataFrame
st.write("### Stock Market Data")
st.write(df)

# Plot the Fear Index
st.write("### Fear Index Over Time")
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(df['Date'], df['Fear Index'], label='Fear Index', color='red')
ax.fill_between(df['Date'], df['Fear Index'], color='red', alpha=0.1)
ax.set_xlabel('Date')
ax.set_ylabel('Fear Index')
ax.legend()
ax.grid(True)
st.pyplot(fig)

# Plot the Greed Index
st.write("### Greed Index Over Time")
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(df['Date'], df['Greed Index'], label='Greed Index', color='blue')
ax.fill_between(df['Date'], df['Greed Index'], color='blue', alpha=0.1)
ax.set_xlabel('Date')
ax.set_ylabel('Greed Index')
ax.legend()
ax.grid(True)
st.pyplot(fig)

# Plot the Trade Potential
st.write("### Trade Potential Over Time")
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(df['Date'], df['Trade Potential'], label='Trade Potential', color='green')
ax.fill_between(df['Date'], df['Trade Potential'], color='green', alpha=0.1)
ax.set_xlabel('Date')
ax.set_ylabel('Trade Potential')
ax.legend()
ax.grid(True)
st.pyplot(fig)
