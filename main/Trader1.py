#!/usr/bin/env python
# coding: utf-8

# In[3]:


import numpy as np
import random

class QLearningBot:
    def __init__(self, action_space):
        self.action_space = action_space
        self.q_table = {}
        self.alpha = 0.5
        self.gamma = 0.6
        self.epsilon = 0.1

    def get_q_value(self, state, action):
        return self.q_table.get((state, action), 0.0)

    def update_q_value(self, state, action, reward, next_state):
        max_q_next_state = max([self.get_q_value(next_state, a) for a in range(self.action_space.n)])
        current_q = self.get_q_value(state, action)
        new_q = current_q + self.alpha * (reward + self.gamma * max_q_next_state - current_q)
        self.q_table[(state, action)] = new_q

    def get_action(self, state):
        if random.uniform(0, 1) < self.epsilon:
            return self.action_space.sample()  # explore
        else:
            return np.argmax([self.get_q_value(state, a) for a in range(self.action_space.n)])  # exploit


# In[ ]:




