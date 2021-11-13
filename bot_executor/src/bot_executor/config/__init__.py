import os
import logging
import logging.config


def get_logging_level():
    return os.getenv("LOGGING_LEVEL", "INFO")


def configure_logging():
    logging.config.dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {
                    "format": "[%(asctime)s] [%(levelname)s] [%(module)s]: #%(funcName)s @%(lineno)d: %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                }
            },
            "handlers": {
                "wsgi": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://flask.logging.wsgi_errors_stream",
                    "formatter": "default",
                }
            },
            "root": {"level": get_logging_level(), "handlers": ["wsgi"]},
        }
    )
