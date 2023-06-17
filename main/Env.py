#!/usr/bin/env python
# coding: utf-8

# In[3]:


import gym
from gym import spaces
import numpy as np

class TradingEnv(gym.Env):
    def __init__(self, prices, initial_balance=10000, max_buy=100, max_sell=100):
        super(TradingEnv, self).__init__()

        self.prices = prices
        self.initial_balance = initial_balance
        self.max_buy = max_buy
        self.max_sell = max_sell

        self.action_space = spaces.MultiDiscrete([3, max(max_buy, max_sell)])  # 0: hold, 1: buy, 2: sell

        self.observation_space = spaces.Box(low=0, high=np.inf, shape=(2,))  # [current_balance, current_asset_value]

    def step(self, action):
        action_type = action[0]
        action_amount = action[1]

        asset_value = self.balance / self.prices[self.current_step]

        reward = 0

        if action_type == 1:  # buy
            action_amount = min(action_amount, self.balance // self.prices[self.current_step])
            self.balance -= action_amount * self.prices[self.current_step]
            reward = -action_amount * self.prices[self.current_step]
        elif action_type == 2:  # sell
            action_amount = min(action_amount, asset_value)
            self.balance += action_amount * self.prices[self.current_step]
            reward = action_amount * self.prices[self.current_step]

        self.current_step += 1
        done = self.balance <= 0 or self.current_step >= len(self.prices)

        return np.array([self.balance, asset_value]), reward, done, {}

    def reset(self):
        self.balance = self.initial_balance
        self.current_step = 0
        return np.array([self.balance, 0])

    def render(self):
        print(f'Step: {self.current_step}, Balance: {self.balance}')


# In[ ]:




