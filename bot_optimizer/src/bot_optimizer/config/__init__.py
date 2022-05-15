import os
import json
import logging
import functools
import logging.config
from firebase_admin import firestore


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


SQL_KEYS = [
    'DARIUSDB_HOST',
    'DARIUSDB_USER',
    'DARIUSDB_PASSWD',
    'DARIUSDB_DB',
    'DARIUSDB_PORT',
]


@functools.lru_cache(maxsize=None)
def get_db_config_from_firestore():
    db = firestore.Client()
    sql_config = db.collection("config").document("sql").get().to_dict()
    return sql_config


@functools.lru_cache(maxsize=None)
def get_db_config_from_env():
    return {key: os.environ.get(key) for key in SQL_KEYS}


@functools.lru_cache(maxsize=None)
def get_db_uri():
    db_config = get_db_config_from_env()
    db_config.update(get_db_config_from_firestore())

    for key in SQL_KEYS:
        if key not in db_config or db_config[key] is None:
            raise Exception("SQL config invalid")

    db_user = db_config.get('DARIUSDB_USER')
    db_password = db_config.get('DARIUSDB_PASSWD')
    db_name = db_config.get('DARIUSDB_DB')
    db_host = db_config.get('DARIUSDB_HOST')
    db_port = db_config.get('DARIUSDB_PORT')
    db_uri = f"mysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    logging.info(f"DB_URI: {db_uri}")
    return db_uri


Hyperopt_Loss = [
    'OnlyProfitHyperOptLoss',
    'SharpeHyperOptLoss',
    'MaxDrawDownHyperOptLoss'
]
