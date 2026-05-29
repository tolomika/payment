import asyncio
import functools


def async_retry(max_retries: int = 3, delay: float = 1, backoff: int = 2):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):

            current_delay = delay

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)

                except Exception:
                    if attempt == max_retries - 1:
                        raise

                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

        return wrapper
    return decorator
