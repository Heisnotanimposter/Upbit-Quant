#!/usr/bin/env python
# coding: utf-8

# In[3]:


importimport pyupbit
import pandas as pd

def fetch_data(ticker):
    df = pyupbit.get_ohlcv(ticker)
    df.to_csv(f'{ticker}_data.csv')
    print("Data fetched successfully")

fetch_data("KRW-BTC")


# In[ ]:




