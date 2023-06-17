#!/usr/bin/env python
# coding: utf-8

# In[3]:


env = TradingEnv(prices)
bot = QLearningBot(env.action_space)

for episode in range(1000):  # number of episodes
    state = env.reset()
    done = False
    while not done:
        action = bot.get_action(state)
        next_state, reward, done, _ = env.step(action)
        bot.update_q_value(state, action, reward, next_state)
        state = next_state


# In[ ]:




