import logging

import structlog

_logger_initialized = False


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    global _logger_initialized
    if not _logger_initialized:
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        structlog.configure(
            processors=[
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        _logger_initialized = True

    return structlog.get_logger(name)
