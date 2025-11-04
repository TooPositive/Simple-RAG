"""
Rate limit handling utilities for OpenAI API.
"""
import time
import re
from typing import Callable, Any, Optional


def extract_retry_after(error_message: str) -> int:
    """
    Extract retry-after seconds from error message.
    
    Args:
        error_message: Error message from API
    
    Returns:
        int: Seconds to wait (default 2 if not found)
    """
    # Look for "retry after X seconds"
    match = re.search(r'retry after (\d+) seconds', error_message.lower())
    if match:
        return int(match.group(1))
    
    # Look for "Please retry after X seconds"
    match = re.search(r'please retry after (\d+) seconds', error_message.lower())
    if match:
        return int(match.group(1))
    
    # Default to 2 seconds
    return 2


async def retry_with_rate_limit(
    func: Callable,
    *args,
    max_retries: int = 3,
    **kwargs
) -> Optional[Any]:
    """
    Retry a function with exponential backoff for rate limits.
    
    Args:
        func: Async function to call
        *args: Function arguments
        max_retries: Maximum retry attempts
        **kwargs: Function keyword arguments
    
    Returns:
        Function result or None if all retries failed
    """
    for attempt in range(max_retries):
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            error_str = str(e)
            
            # Check if it's a rate limit error
            if '429' in error_str or 'rate limit' in error_str.lower():
                if attempt < max_retries - 1:
                    # Extract wait time from error message
                    wait_time = extract_retry_after(error_str)
                    
                    # Add exponential backoff
                    wait_time *= (attempt + 1)
                    
                    print(f"  ⏳ Rate limit reached - waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                    time.sleep(wait_time)
                    continue
                else:
                    # Last attempt failed
                    print(f"  ❌ Rate limit error after {max_retries} retries")
                    return None
            else:
                # Not a rate limit error, re-raise
                raise e
    
    return None


def format_rate_limit_message(error_message: str) -> str:
    """
    Format a user-friendly rate limit message.
    
    Args:
        error_message: Raw error message from API
    
    Returns:
        str: User-friendly message
    """
    wait_time = extract_retry_after(error_message)
    
    return (
        f"⏳ We're experiencing high demand right now.\n"
        f"   Please wait approximately {wait_time} seconds and try again.\n"
        f"   This helps ensure fair access for everyone."
    )
