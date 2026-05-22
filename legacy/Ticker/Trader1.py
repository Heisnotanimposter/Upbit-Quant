"""
Modern Q-Learning trading bot implementation for UPbit Quantitative Trading Platform.
"""

import numpy as np
import random
from typing import Tuple, Dict, Any, Optional, List
from dataclasses import dataclass
from abc import ABC, abstractmethod

from upbit_quant.core.logger import get_logger
from upbit_quant.core.exceptions import TradingError, ValidationError
from upbit_quant.utils.validation import validate_positive_number
from upbit_quant.utils.decorators import log_execution_time, cache_result


logger = get_logger(__name__)


@dataclass
class QLearningConfig:
    """Configuration for Q-Learning bot."""
    alpha: float = 0.5  # Learning rate
    gamma: float = 0.6  # Discount factor
    epsilon: float = 0.1  # Exploration rate
    epsilon_decay: float = 0.995  # Epsilon decay rate
    epsilon_min: float = 0.01  # Minimum epsilon
    memory_size: int = 10000  # Experience replay buffer size
    batch_size: int = 32  # Batch size for training


class TradingBot(ABC):
    """Abstract base class for trading bots."""
    
    @abstractmethod
    def get_action(self, state: np.ndarray) -> np.ndarray:
        """Get action for given state."""
        pass
    
    @abstractmethod
    def update(self, state: np.ndarray, action: np.ndarray, reward: float, next_state: np.ndarray) -> None:
        """Update bot with new experience."""
        pass
    
    @abstractmethod
    def save_model(self, filepath: str) -> None:
        """Save model to file."""
        pass
    
    @abstractmethod
    def load_model(self, filepath: str) -> None:
        """Load model from file."""
        pass


class QLearningBot(TradingBot):
    """
    Modern Q-Learning trading bot with improved features.
    
    Features:
    - Experience replay
    - Epsilon decay
    - State discretization
    - Performance tracking
    - Model persistence
    """
    
    def __init__(
        self, 
        action_space: Any, 
        config: Optional[QLearningConfig] = None,
        state_bins: int = 10
    ):
        """
        Initialize Q-Learning bot.
        
        Args:
            action_space: Gym action space
            config: Q-Learning configuration
            state_bins: Number of bins for state discretization
            
        Raises:
            ValidationError: If parameters are invalid
        """
        self.action_space = action_space
        self.config = config or QLearningConfig()
        self.state_bins = validate_positive_number(state_bins, "state_bins")
        
        # Validate config parameters
        self.config.alpha = validate_positive_number(self.config.alpha, "alpha")
        self.config.gamma = validate_positive_number(self.config.gamma, "gamma")
        self.config.epsilon = validate_positive_number(self.config.epsilon, "epsilon")
        
        # Initialize Q-table and experience replay
        self.q_table: Dict[Tuple, float] = {}
        self.experience_buffer: List[Tuple] = []
        self.training_episodes = 0
        self.total_reward = 0.0
        
        # Performance tracking
        self.performance_history: List[Dict[str, float]] = []
        
        logger.info(f"Q-Learning bot initialized with config: {self.config}")
    
    def _discretize_state(self, state: np.ndarray) -> Tuple:
        """
        Discretize continuous state for Q-table lookup.
        
        Args:
            state: Continuous state array
            
        Returns:
            Discretized state tuple
        """
        try:
            # Normalize and discretize each dimension
            discretized = []
            for i, value in enumerate(state):
                # Simple binning - in practice, you might want more sophisticated discretization
                bin_index = min(int(value * self.state_bins), self.state_bins - 1)
                discretized.append(max(0, bin_index))
            
            return tuple(discretized)
        except Exception as e:
            logger.error(f"Error discretizing state {state}: {e}")
            return tuple([0] * len(state))
    
    @cache_result(ttl=60)  # Cache for 1 minute
    def get_q_value(self, state: np.ndarray, action: int) -> float:
        """
        Get Q-value for state-action pair.
        
        Args:
            state: State array
            action: Action index
            
        Returns:
            Q-value
        """
        discretized_state = self._discretize_state(state)
        return self.q_table.get((discretized_state, action), 0.0)
    
    def update_q_value(
        self, 
        state: np.ndarray, 
        action: int, 
        reward: float, 
        next_state: np.ndarray
    ) -> None:
        """
        Update Q-value using Q-learning algorithm.
        
        Args:
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Next state
        """
        try:
            discretized_state = self._discretize_state(state)
            discretized_next_state = self._discretize_state(next_state)
            
            # Calculate target Q-value
            max_q_next_state = max([
                self.get_q_value(next_state, a) 
                for a in range(self.action_space.n)
            ])
            
            current_q = self.get_q_value(state, action)
            target_q = reward + self.config.gamma * max_q_next_state
            
            # Update Q-value
            new_q = current_q + self.config.alpha * (target_q - current_q)
            self.q_table[(discretized_state, action)] = new_q
            
            # Add experience to replay buffer
            self.experience_buffer.append((state, action, reward, next_state))
            if len(self.experience_buffer) > self.config.memory_size:
                self.experience_buffer.pop(0)
            
            # Update performance tracking
            self.total_reward += reward
            
        except Exception as e:
            logger.error(f"Error updating Q-value: {e}")
            raise TradingError(f"Failed to update Q-value: {e}") from e
    
    @log_execution_time
    def get_action(self, state: np.ndarray) -> np.ndarray:
        """
        Get action using epsilon-greedy policy.
        
        Args:
            state: Current state
            
        Returns:
            Action array [action_type, action_amount]
        """
        try:
            # Epsilon-greedy action selection
            if random.uniform(0, 1) < self.config.epsilon:
                # Explore: random action
                action_type = random.randint(0, 2)  # 0: hold, 1: buy, 2: sell
                action_amount = random.randint(1, 100)  # Random amount
                action = np.array([action_type, action_amount])
            else:
                # Exploit: best action based on Q-values
                q_values = [
                    self.get_q_value(state, a) 
                    for a in range(self.action_space.n)
                ]
                best_action = np.argmax(q_values)
                
                # Convert single action to action array
                if best_action == 0:  # hold
                    action = np.array([0, 0])
                elif best_action == 1:  # buy
                    action = np.array([1, random.randint(1, 50)])
                else:  # sell
                    action = np.array([2, random.randint(1, 50)])
            
            logger.debug(f"Selected action: {action}, epsilon: {self.config.epsilon:.3f}")
            return action
            
        except Exception as e:
            logger.error(f"Error getting action: {e}")
            # Return safe action (hold)
            return np.array([0, 0])
    
    def update(self, state: np.ndarray, action: np.ndarray, reward: float, next_state: np.ndarray) -> None:
        """
        Update bot with new experience.
        
        Args:
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Next state
        """
        action_index = int(action[0])  # Convert action array to index
        self.update_q_value(state, action_index, reward, next_state)
    
    def decay_epsilon(self) -> None:
        """Decay exploration rate."""
        self.config.epsilon = max(
            self.config.epsilon_min,
            self.config.epsilon * self.config.epsilon_decay
        )
    
    def train_episode(self, env) -> Dict[str, float]:
        """
        Train bot for one episode.
        
        Args:
            env: Trading environment
            
        Returns:
            Episode performance metrics
        """
        state = env.reset()
        done = False
        episode_reward = 0.0
        step_count = 0
        
        while not done and step_count < 1000:  # Prevent infinite episodes
            action = self.get_action(state)
            next_state, reward, done, info = env.step(action)
            
            self.update(state, action, reward, next_state)
            
            state = next_state
            episode_reward += reward
            step_count += 1
        
        # Decay epsilon after episode
        self.decay_epsilon()
        self.training_episodes += 1
        
        # Record performance
        episode_metrics = {
            'episode': self.training_episodes,
            'reward': episode_reward,
            'steps': step_count,
            'epsilon': self.config.epsilon,
            'q_table_size': len(self.q_table)
        }
        self.performance_history.append(episode_metrics)
        
        logger.info(f"Episode {self.training_episodes}: Reward={episode_reward:.2f}, "
                   f"Steps={step_count}, Epsilon={self.config.epsilon:.3f}")
        
        return episode_metrics
    
    def get_performance_summary(self) -> Dict[str, float]:
        """
        Get performance summary.
        
        Returns:
            Performance summary dictionary
        """
        if not self.performance_history:
            return {}
        
        recent_rewards = [ep['reward'] for ep in self.performance_history[-10:]]
        
        return {
            'total_episodes': self.training_episodes,
            'total_reward': self.total_reward,
            'average_reward': np.mean(recent_rewards) if recent_rewards else 0,
            'best_reward': max(recent_rewards) if recent_rewards else 0,
            'current_epsilon': self.config.epsilon,
            'q_table_size': len(self.q_table)
        }
    
    def save_model(self, filepath: str) -> None:
        """
        Save model to file.
        
        Args:
            filepath: Path to save model
        """
        try:
            import pickle
            
            model_data = {
                'q_table': self.q_table,
                'config': self.config,
                'training_episodes': self.training_episodes,
                'total_reward': self.total_reward,
                'performance_history': self.performance_history
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            
            logger.info(f"Model saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            raise TradingError(f"Failed to save model: {e}") from e
    
    def load_model(self, filepath: str) -> None:
        """
        Load model from file.
        
        Args:
            filepath: Path to load model from
        """
        try:
            import pickle
            
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.q_table = model_data['q_table']
            self.config = model_data['config']
            self.training_episodes = model_data['training_episodes']
            self.total_reward = model_data['total_reward']
            self.performance_history = model_data['performance_history']
            
            logger.info(f"Model loaded from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise TradingError(f"Failed to load model: {e}") from e
    
    def reset(self) -> None:
        """Reset bot to initial state."""
        self.q_table.clear()
        self.experience_buffer.clear()
        self.training_episodes = 0
        self.total_reward = 0.0
        self.performance_history.clear()
        self.config.epsilon = 0.1  # Reset epsilon
        
        logger.info("Q-Learning bot reset")




