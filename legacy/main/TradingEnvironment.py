"""
Modern trading environment implementation for UPbit Quantitative Trading Platform.
"""

import gym
from gym import spaces
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from upbit_quant.core.logger import get_logger
from upbit_quant.core.exceptions import TradingError, ValidationError
from upbit_quant.utils.validation import validate_positive_number
from upbit_quant.utils.decorators import log_execution_time


logger = get_logger(__name__)


class ActionType(Enum):
    """Action types for trading environment."""
    HOLD = 0
    BUY = 1
    SELL = 2


@dataclass
class TradingState:
    """Trading state information."""
    balance: float
    asset_value: float
    current_step: int
    total_value: float
    position_size: float


class TradingEnv(gym.Env):
    """
    Modern trading environment with improved structure and error handling.
    
    This environment provides a gym-compatible interface for trading simulations
    with proper state management and validation.
    """
    
    def __init__(
        self, 
        prices: List[float], 
        initial_balance: float = 10000.0, 
        max_buy: float = 100.0, 
        max_sell: float = 100.0,
        trading_fee: float = 0.0005
    ):
        """
        Initialize trading environment.
        
        Args:
            prices: List of price data for trading simulation
            initial_balance: Initial balance for trading
            max_buy: Maximum buy amount per trade
            max_sell: Maximum sell amount per trade
            trading_fee: Trading fee as percentage (0.0005 = 0.05%)
            
        Raises:
            ValidationError: If input parameters are invalid
        """
        super().__init__()
        
        # Validate inputs
        self.prices = self._validate_prices(prices)
        self.initial_balance = validate_positive_number(initial_balance, "initial_balance")
        self.max_buy = validate_positive_number(max_buy, "max_buy")
        self.max_sell = validate_positive_number(max_sell, "max_sell")
        self.trading_fee = validate_positive_number(trading_fee, "trading_fee")
        
        # Initialize state
        self.balance = self.initial_balance
        self.current_step = 0
        self.position_size = 0.0
        self.total_trades = 0
        self.total_fees = 0.0
        
        # Define action and observation spaces
        self.action_space = spaces.MultiDiscrete([3, max(max_buy, max_sell)])
        self.observation_space = spaces.Box(
            low=0, 
            high=np.inf, 
            shape=(4,), 
            dtype=np.float32
        )  # [balance, asset_value, position_size, current_price]
        
        logger.info(f"Trading environment initialized with {len(prices)} price points")
    
    def _validate_prices(self, prices: List[float]) -> List[float]:
        """Validate price data."""
        if not prices or len(prices) == 0:
            raise ValidationError("Price data cannot be empty")
        
        if not all(isinstance(p, (int, float)) and p > 0 for p in prices):
            raise ValidationError("All prices must be positive numbers")
        
        return list(prices)
    
    @log_execution_time
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """
        Execute one step in the trading environment.
        
        Args:
            action: Action array [action_type, action_amount]
            
        Returns:
            Tuple of (observation, reward, done, info)
            
        Raises:
            TradingError: If action execution fails
        """
        try:
            action_type = ActionType(action[0])
            action_amount = float(action[1])
            
            # Validate action
            if action_amount < 0:
                raise ValidationError("Action amount cannot be negative")
            
            current_price = self.prices[self.current_step]
            asset_value = self.position_size * current_price
            total_value = self.balance + asset_value
            
            reward = 0.0
            trade_executed = False
            
            # Execute action
            if action_type == ActionType.BUY and self.balance > 0:
                reward, trade_executed = self._execute_buy(action_amount, current_price)
            elif action_type == ActionType.SELL and self.position_size > 0:
                reward, trade_executed = self._execute_sell(action_amount, current_price)
            
            # Move to next step
            self.current_step += 1
            done = self._is_done()
            
            # Calculate new state
            new_asset_value = self.position_size * self.prices[min(self.current_step, len(self.prices) - 1)]
            new_total_value = self.balance + new_asset_value
            
            # Create observation
            observation = np.array([
                self.balance,
                new_asset_value,
                self.position_size,
                current_price
            ], dtype=np.float32)
            
            # Create info dictionary
            info = {
                'total_value': new_total_value,
                'total_trades': self.total_trades,
                'total_fees': self.total_fees,
                'trade_executed': trade_executed,
                'action_type': action_type.name,
                'action_amount': action_amount
            }
            
            logger.debug(f"Step {self.current_step}: Balance={self.balance:.2f}, "
                        f"Position={self.position_size:.2f}, Reward={reward:.2f}")
            
            return observation, reward, done, info
            
        except Exception as e:
            logger.error(f"Error executing action {action}: {e}")
            raise TradingError(f"Failed to execute action: {e}") from e
    
    def _execute_buy(self, amount: float, price: float) -> Tuple[float, bool]:
        """Execute buy action."""
        max_buyable = self.balance / price
        actual_amount = min(amount, max_buyable, self.max_buy)
        
        if actual_amount > 0:
            cost = actual_amount * price
            fee = cost * self.trading_fee
            total_cost = cost + fee
            
            if total_cost <= self.balance:
                self.balance -= total_cost
                self.position_size += actual_amount
                self.total_trades += 1
                self.total_fees += fee
                
                # Reward based on position increase
                reward = actual_amount * price * 0.01  # Small positive reward for buying
                return reward, True
        
        return 0.0, False
    
    def _execute_sell(self, amount: float, price: float) -> Tuple[float, bool]:
        """Execute sell action."""
        actual_amount = min(amount, self.position_size, self.max_sell)
        
        if actual_amount > 0:
            revenue = actual_amount * price
            fee = revenue * self.trading_fee
            net_revenue = revenue - fee
            
            self.balance += net_revenue
            self.position_size -= actual_amount
            self.total_trades += 1
            self.total_fees += fee
            
            # Reward based on revenue
            reward = net_revenue * 0.01  # Small positive reward for selling
            return reward, True
        
        return 0.0, False
    
    def _is_done(self) -> bool:
        """Check if episode is done."""
        return (
            self.balance <= 0 or 
            self.current_step >= len(self.prices) - 1 or
            self.position_size <= 0 and self.balance <= 0
        )
    
    def reset(self) -> np.ndarray:
        """
        Reset environment to initial state.
        
        Returns:
            Initial observation
        """
        self.balance = self.initial_balance
        self.current_step = 0
        self.position_size = 0.0
        self.total_trades = 0
        self.total_fees = 0.0
        
        logger.info("Trading environment reset")
        
        return np.array([
            self.balance,
            0.0,  # asset_value
            0.0,  # position_size
            self.prices[0]  # current_price
        ], dtype=np.float32)
    
    def render(self, mode: str = 'human') -> Optional[str]:
        """
        Render the current state of the environment.
        
        Args:
            mode: Render mode ('human' or 'rgb_array')
            
        Returns:
            Rendered output or None
        """
        current_price = self.prices[min(self.current_step, len(self.prices) - 1)]
        asset_value = self.position_size * current_price
        total_value = self.balance + asset_value
        
        state_info = (
            f"Step: {self.current_step}/{len(self.prices)-1}, "
            f"Balance: ${self.balance:.2f}, "
            f"Position: {self.position_size:.4f}, "
            f"Asset Value: ${asset_value:.2f}, "
            f"Total Value: ${total_value:.2f}, "
            f"Current Price: ${current_price:.2f}, "
            f"Total Trades: {self.total_trades}, "
            f"Total Fees: ${self.total_fees:.2f}"
        )
        
        if mode == 'human':
            print(state_info)
        elif mode == 'rgb_array':
            return state_info
        
        return None
    
    def get_state(self) -> TradingState:
        """
        Get current trading state.
        
        Returns:
            Current trading state
        """
        current_price = self.prices[min(self.current_step, len(self.prices) - 1)]
        asset_value = self.position_size * current_price
        total_value = self.balance + asset_value
        
        return TradingState(
            balance=self.balance,
            asset_value=asset_value,
            current_step=self.current_step,
            total_value=total_value,
            position_size=self.position_size
        )
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """
        Get performance metrics for the current episode.
        
        Returns:
            Dictionary of performance metrics
        """
        current_price = self.prices[min(self.current_step, len(self.prices) - 1)]
        asset_value = self.position_size * current_price
        total_value = self.balance + asset_value
        
        # Calculate returns
        total_return = (total_value - self.initial_balance) / self.initial_balance
        
        # Calculate price return (buy and hold strategy)
        price_return = (current_price - self.prices[0]) / self.prices[0]
        
        # Calculate excess return
        excess_return = total_return - price_return
        
        return {
            'total_return': total_return,
            'price_return': price_return,
            'excess_return': excess_return,
            'total_value': total_value,
            'total_trades': self.total_trades,
            'total_fees': self.total_fees,
            'fee_ratio': self.total_fees / self.initial_balance if self.initial_balance > 0 else 0
        }


# In[ ]:




