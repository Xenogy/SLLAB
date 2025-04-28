"""
Error recovery mechanisms for the AccountDB application.

This module provides functions for recovering from errors, including
retry mechanisms, circuit breakers, fallback handlers, and graceful degradation.
"""

import time
import logging
import functools
import random
from typing import Optional, Dict, List, Any, Union, Callable, Type, TypeVar

from .exceptions import TimeoutError, ExternalServiceError

# Configure logging
logger = logging.getLogger(__name__)

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')

# Circuit breaker states
CIRCUIT_CLOSED = 'closed'  # Normal operation
CIRCUIT_OPEN = 'open'      # Failing, not allowing requests
CIRCUIT_HALF_OPEN = 'half-open'  # Testing if service is back

# Circuit breaker registry
circuit_breakers = {}

def retry_operation(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retrying operations that may fail.
    
    Args:
        max_retries: Maximum number of retries
        retry_delay: Initial delay between retries in seconds
        backoff_factor: Factor to increase delay for each retry
        jitter: Whether to add random jitter to delay
        exceptions: Exception types to catch and retry
        
    Returns:
        Callable: Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        # Calculate delay with exponential backoff
                        delay = retry_delay * (backoff_factor ** attempt)
                        
                        # Add jitter if enabled
                        if jitter:
                            delay = delay * (0.5 + random.random())
                        
                        # Log retry attempt
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                            f"after {delay:.2f}s due to {type(e).__name__}: {str(e)}"
                        )
                        
                        # Wait before retrying
                        time.sleep(delay)
                    else:
                        # Log final failure
                        logger.error(
                            f"Failed all {max_retries} retries for {func.__name__} "
                            f"due to {type(e).__name__}: {str(e)}"
                        )
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    
    return decorator

class CircuitBreaker:
    """Circuit breaker for protecting against failing services."""
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        recovery_threshold: int = 2,
        timeout: float = 10.0
    ):
        """
        Initialize a circuit breaker.
        
        Args:
            name: Name of the circuit breaker
            failure_threshold: Number of failures before opening the circuit
            recovery_timeout: Time in seconds to wait before testing recovery
            recovery_threshold: Number of successful tests before closing the circuit
            timeout: Timeout in seconds for operations
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.recovery_threshold = recovery_threshold
        self.timeout = timeout
        
        self.state = CIRCUIT_CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.last_test_time = 0
        
        # Register this circuit breaker
        circuit_breakers[name] = self
    
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Decorator for protecting a function with a circuit breaker.
        
        Args:
            func: The function to protect
            
        Returns:
            Callable: The protected function
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            return self.call(func, *args, **kwargs)
        
        return wrapper
    
    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Call a function with circuit breaker protection.
        
        Args:
            func: The function to call
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            T: The result of the function
            
        Raises:
            ExternalServiceError: If the circuit is open
        """
        # Check if circuit is open
        if self.state == CIRCUIT_OPEN:
            # Check if recovery timeout has elapsed
            if time.time() - self.last_failure_time > self.recovery_timeout:
                # Transition to half-open state
                logger.info(f"Circuit {self.name} transitioning from OPEN to HALF-OPEN")
                self.state = CIRCUIT_HALF_OPEN
                self.success_count = 0
            else:
                # Circuit is still open, fail fast
                raise ExternalServiceError(
                    message=f"Circuit {self.name} is OPEN",
                    service=self.name
                )
        
        # If we're here, the circuit is either CLOSED or HALF-OPEN
        try:
            # Set a timeout for the operation
            start_time = time.time()
            
            # Call the function
            result = func(*args, **kwargs)
            
            # Check if operation timed out
            if time.time() - start_time > self.timeout:
                raise TimeoutError(
                    message=f"Operation timed out",
                    operation=func.__name__,
                    timeout=self.timeout
                )
            
            # Operation succeeded
            self._handle_success()
            return result
        except Exception as e:
            # Operation failed
            self._handle_failure(e)
            raise
    
    def _handle_success(self) -> None:
        """Handle a successful operation."""
        if self.state == CIRCUIT_HALF_OPEN:
            # Increment success count
            self.success_count += 1
            
            # Check if we've reached the recovery threshold
            if self.success_count >= self.recovery_threshold:
                # Transition to closed state
                logger.info(f"Circuit {self.name} transitioning from HALF-OPEN to CLOSED")
                self.state = CIRCUIT_CLOSED
                self.failure_count = 0
        elif self.state == CIRCUIT_CLOSED:
            # Reset failure count
            self.failure_count = 0
    
    def _handle_failure(self, exception: Exception) -> None:
        """
        Handle a failed operation.
        
        Args:
            exception: The exception that occurred
        """
        # Record failure time
        self.last_failure_time = time.time()
        
        if self.state == CIRCUIT_CLOSED:
            # Increment failure count
            self.failure_count += 1
            
            # Check if we've reached the failure threshold
            if self.failure_count >= self.failure_threshold:
                # Transition to open state
                logger.warning(
                    f"Circuit {self.name} transitioning from CLOSED to OPEN "
                    f"due to {type(exception).__name__}: {str(exception)}"
                )
                self.state = CIRCUIT_OPEN
        elif self.state == CIRCUIT_HALF_OPEN:
            # Transition back to open state
            logger.warning(
                f"Circuit {self.name} transitioning from HALF-OPEN to OPEN "
                f"due to {type(exception).__name__}: {str(exception)}"
            )
            self.state = CIRCUIT_OPEN

def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    recovery_threshold: int = 2,
    timeout: float = 10.0
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for protecting a function with a circuit breaker.
    
    Args:
        name: Name of the circuit breaker
        failure_threshold: Number of failures before opening the circuit
        recovery_timeout: Time in seconds to wait before testing recovery
        recovery_threshold: Number of successful tests before closing the circuit
        timeout: Timeout in seconds for operations
        
    Returns:
        Callable: Decorator function
    """
    # Check if circuit breaker already exists
    if name in circuit_breakers:
        cb = circuit_breakers[name]
    else:
        # Create a new circuit breaker
        cb = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            recovery_threshold=recovery_threshold,
            timeout=timeout
        )
    
    # Return the decorator
    return cb

def fallback_handler(
    fallback_function: Callable[..., R],
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    Decorator for providing a fallback when a function fails.
    
    Args:
        fallback_function: Function to call as a fallback
        exceptions: Exception types to catch
        
    Returns:
        Callable: Decorator function
    """
    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> R:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                # Log the exception
                logger.warning(
                    f"Falling back from {func.__name__} to {fallback_function.__name__} "
                    f"due to {type(e).__name__}: {str(e)}"
                )
                
                # Call the fallback function
                return fallback_function(*args, **kwargs)
        
        return wrapper
    
    return decorator

def graceful_degradation(
    degraded_function: Callable[..., R],
    exceptions: Union[Type[Exception], List[Type[Exception]]] = Exception
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    Decorator for gracefully degrading functionality when a function fails.
    
    Args:
        degraded_function: Function to call for degraded functionality
        exceptions: Exception types to catch
        
    Returns:
        Callable: Decorator function
    """
    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> R:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                # Log the exception
                logger.warning(
                    f"Degrading from {func.__name__} to {degraded_function.__name__} "
                    f"due to {type(e).__name__}: {str(e)}"
                )
                
                # Call the degraded function
                return degraded_function(*args, **kwargs)
        
        return wrapper
    
    return decorator
