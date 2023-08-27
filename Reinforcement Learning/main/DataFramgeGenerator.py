#!/usr/bin/env python
# coding: utf-8

# In[2]:


import pandas as pd
import numpy as np

# Set a seed for reproducibility
np.random.seed(0)

# Create a date range
date_range = pd.date_range(end='today', periods=100)

# Create random price data
btc = np.random.randint(30000, 40000, size=100) + np.random.random(size=100)
eth = np.random.randint(2000, 3000, size=100) + np.random.random(size=100)
xrp = np.random.randint(0, 2, size=100) + np.random.random(size=100)
ltc = np.random.randint(100, 200, size=100) + np.random.random(size=100)
bch = np.random.randint(500, 600, size=100) + np.random.random(size=100)

# Combine into a DataFrame
df = pd.DataFrame(data={'BTC': btc, 'ETH': eth, 'XRP': xrp, 'LTC': ltc, 'BCH': bch}, index=date_range)

print(df.head())


# In[ ]:




