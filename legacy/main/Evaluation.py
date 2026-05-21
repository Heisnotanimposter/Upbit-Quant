#!/usr/bin/env python
# coding: utf-8

# In[1]:


def evaluate_bot(env, bot, num_episodes=100):
    total_rewards = []
    for episode in range(num_episodes):
        state = env.reset()
        done = False
        total_reward = 0
        while not done:
            action = bot.get_action(state)
            next_state, reward, done, _ = env.step(action)
            state = next_state
            total_reward += reward
        total_rewards.append(total_reward)
    return np.mean(total_rewards), np.std(total_rewards)

prices = ...  # Your list of historical prices
env = TradingEnv(prices)
bot = QLearningBot(env.action_space)

mean_reward, std_reward = evaluate_bot(env, bot)
print(f'Mean reward: {mean_reward}, Std reward: {std_reward}')


# In[ ]:




