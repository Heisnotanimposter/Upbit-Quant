#!/usr/bin/env python
# coding: utf-8

# In[ ]:


def backtest(env, bot):
    state = env.reset()
    done = False
    total_reward = 0
    while not done:
        action = bot.get_action(state)
        next_state, reward, done, _ = env.step(action)
        state = next_state
        total_reward += reward
    return total_reward

# Train the bot before backtesting
for episode in range(1000):  # number of episodes
    state = env.reset()
    done = False
    while not done:
        action = bot.get_action(state)
        next_state, reward, done, _ = env.step(action)
        bot.update_q_value(state, action, reward, next_state)
        state = next_state

# Backtest the bot
total_reward = backtest(env, bot)
print(f'Total reward from backtest: {total_reward}')

