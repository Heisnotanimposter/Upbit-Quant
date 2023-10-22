#!/usr/bin/env python
# coding: utf-8

# In[2]:


def run_simulation(env, bot):
    state = env.reset()
    done = False
    while not done:
        action = bot.get_action(state)
        next_state, reward, done, _ = env.step(action)
        bot.update_q_value(state, action, reward, next_state)
        state = next_state
        env.render()

prices = ...  # Your list of historical prices
env = TradingEnv(prices)
bot = QLearningBot(env.action_space)

run_simulation(env, bot)


# In[ ]:




