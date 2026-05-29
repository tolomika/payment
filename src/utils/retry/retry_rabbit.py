from functools import wraps

def rabbitmq_retry(max_retries: int = 3, retry_header: str = "x-retry"):
    def decorator(func):
        @wraps(func)
        async def wrapper(message, *args, **kwargs):
            async with message.process(ignore_processed=True):

                retries = message.headers.get(retry_header, 0)

                try:
                    return await func(message, *args, **kwargs)

                except Exception as e:
                    if retries >= max_retries:
                        # send in DLQ
                        await message.reject(requeue=False)
                        return

                    await message.channel.default_exchange.publish(
                        message.__class__(
                            body=message.body,
                            headers={
                                **(message.headers or {}),
                                retry_header: retries + 1,
                            },
                        ),
                        routing_key=message.routing_key,
                    )

                    await message.ack()

        return wrapper
    return decorator
