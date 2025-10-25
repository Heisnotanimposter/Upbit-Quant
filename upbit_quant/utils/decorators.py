"""
Decorators for UPbit Quantitative Trading Platform.
"""

import functools
import time
from typing import Any, Callable, Dict, List, Optional, Type, Union
from datetime import datetime

from ..core.exceptions import UPbitQuantError
from ..core.logger import get_logger


logger = get_logger(__name__)


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """Decorator to retry function on failure.
    
    Args:
        max_retries: Maximum number of retries
        delay: Initial delay between retries in seconds
        backoff_factor: Factor to multiply delay by after each retry
        exceptions: Tuple of exceptions to catch and retry on
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        raise
                    
                    logger.warning(f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
            
            return None
        return wrapper
    return decorator


def log_execution_time(func: Callable) -> Callable:
    """Decorator to log function execution time.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"Function {func.__name__} executed in {execution_time:.4f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Function {func.__name__} failed after {execution_time:.4f} seconds: {e}")
            raise
    return wrapper


def validate_inputs(**validators: Callable) -> Callable:
    """Decorator to validate function inputs.
    
    Args:
        **validators: Dictionary mapping parameter names to validator functions
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get function signature
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate inputs
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    try:
                        validated_value = validator(value)
                        bound_args.arguments[param_name] = validated_value
                    except Exception as e:
                        logger.error(f"Validation failed for parameter '{param_name}': {e}")
                        raise
            
            return func(*bound_args.args, **bound_args.kwargs)
        return wrapper
    return decorator


def cache_result(ttl: int = 3600) -> Callable:
    """Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        cache: Dict[str, Dict[str, Any]] = {}
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Create cache key
            import hashlib
            key = hashlib.md5(str(args).encode() + str(kwargs).encode()).hexdigest()
            
            # Check if result is cached and not expired
            if key in cache:
                cached_data = cache[key]
                if time.time() - cached_data['timestamp'] < ttl:
                    logger.debug(f"Cache hit for function {func.__name__}")
                    return cached_data['result']
                else:
                    # Remove expired cache entry
                    del cache[key]
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache[key] = {
                'result': result,
                'timestamp': time.time()
            }
            
            logger.debug(f"Result cached for function {func.__name__}")
            return result
        return wrapper
    return decorator


def rate_limit(calls_per_second: float = 1.0) -> Callable:
    """Decorator to rate limit function calls.
    
    Args:
        calls_per_second: Maximum calls per second
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        last_called = [0.0]
        min_interval = 1.0 / calls_per_second
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator


def handle_exceptions(
    default_return: Any = None,
    exceptions: tuple = (Exception,),
    log_errors: bool = True
) -> Callable:
    """Decorator to handle exceptions gracefully.
    
    Args:
        default_return: Value to return if exception occurs
        exceptions: Tuple of exceptions to catch
        log_errors: Whether to log errors
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if log_errors:
                    logger.error(f"Exception in function {func.__name__}: {e}")
                return default_return
        return wrapper
    return decorator


def deprecated(reason: str = "This function is deprecated") -> Callable:
    """Decorator to mark functions as deprecated.
    
    Args:
        reason: Reason for deprecation
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger.warning(f"DEPRECATED: {func.__name__} is deprecated. {reason}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def singleton(cls: Type) -> Type:
    """Decorator to implement singleton pattern.
    
    Args:
        cls: Class to make singleton
        
    Returns:
        Singleton class
    """
    instances: Dict[Type, Any] = {}
    
    def get_instance(*args: Any, **kwargs: Any) -> Any:
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance


def timeout(seconds: float) -> Callable:
    """Decorator to add timeout to function execution.
    
    Args:
        seconds: Timeout in seconds
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")
            
            # Set the signal handler
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(seconds))
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        
        return wrapper
    return decorator
