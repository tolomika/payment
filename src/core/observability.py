import logging

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

from core.config import config


def setup_sentry(service_name: str) -> None:
    dsn = config.sentry_dsn.get_secret_value()
    if not dsn:
        return

    sentry_sdk.init(
        dsn=dsn,
        integrations=[
            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ],
        traces_sample_rate=1.0,
        environment="DEV" if config.debug else "PROD",
        server_name=service_name,
    )
