import time
import functools
import random

def retry_with_backoff(max_retries=3, initial_delay=1, backoff_factor=2, exceptions=(Exception,)):
    """
    Decorator to retry a function call with exponential backoff.
    
    Args:
        max_retries (int): Maximum number of retries.
        initial_delay (float): Initial delay in seconds.
        backoff_factor (float): Multiplier for delay after each failure.
        exceptions (tuple): Tuple of exceptions to catch and retry.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        print(f"      ❌ [Resilience] {func.__name__} failed after {max_retries} retries. Error: {e}")
                        raise last_exception
                    
                    # Log the retry
                    print(f"      ⚠️ [Resilience] {func.__name__} failed (Attempt {attempt + 1}/{max_retries}). Retrying in {delay}s... Error: {e}")
                    
                    # Sleep with simple jitter
                    sleep_time = delay + random.uniform(0, 0.5)
                    time.sleep(sleep_time)
                    
                    delay *= backoff_factor
            
            return None # Should not be reached
        return wrapper
    return decorator

class CircuitBreaker:
    """
    Simple in-memory circuit breaker.
    If 'failures' exceeds 'threshold', matches are blocked for 'reset_timeout'.
    """
    def __init__(self, failure_threshold=3, reset_timeout=3600):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED" # CLOSED, OPEN
        
    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.reset_timeout:
                print(f"      🔄 [CircuitBreaker] Reset timeout expired. Half-opening...")
                self.state = "HALF_OPEN"
            else:
                print(f"      ⛔ [CircuitBreaker] Circuit is OPEN. Skipping call.")
                return None
                
        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            print(f"      ⚠️ [CircuitBreaker] Call failed ({self.failures}/{self.failure_threshold}). Error: {e}")
            
            if self.failures >= self.failure_threshold:
                self.state = "OPEN"
                print(f"      🔌 [CircuitBreaker] Threshold reached. Circuit OPEN for {self.reset_timeout}s.")
            
            raise e
