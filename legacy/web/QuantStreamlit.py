import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.title('Quant Python Streamlit Example')

# Let's create a DataFrame with random data representing the "Fear Index"
date_range = pd.date_range(start='01-01-2019', end='12-31-2021', freq='B')
fear_index = np.random.randint(low=0, high=100, size=len(date_range))
greed_index = np.random.randint(low=0, high=100, size=len(date_range))


df = pd.DataFrame({'Fear Index': fear_index, 'Greed Index': greed_index}, index=date_range)

st.write(df)

# Plot the data
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(df.index, df['Fear Index'], label='Fear Index', color='red')
ax.fill_between(df.index, df['Fear Index'], color='red', alpha=0.1)
ax.set_title('Stock Market Fear Index Over Time')
ax.set_xlabel('Date')
ax.set_ylabel('Fear Index')
ax.legend()
ax.grid(True)

# Let's create a DataFrame with random data representing the "Fear Index"
date_range = pd.date_range(start='01-01-2019', end='12-31-2021', freq='B')
fear_index = np.random.randint(low=0, high=100, size=len(date_range))

df = pd.DataFrame({'Greed Index': fear_index}, index=date_range)

# Plot the data
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(df.index, df['Greed Index'], label='Greed Index', color='red')
ax.fill_between(df.index, df['Greed Index'], color='red', alpha=0.1)
ax.set_title('Stock Market Greed Index Over Time')
ax.set_xlabel('Date')
ax.set_ylabel('Greed Index')
ax.legend()
ax.grid(True)

# Now we can view our streamlit app in browser
#streamlit run /Users/'your username'/'...'/streamlittest/QuantStreamlit.py


