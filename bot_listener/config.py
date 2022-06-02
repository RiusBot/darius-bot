import os
import yaml
import logging

from worker.services.auth import fetch_backend_url_firestore


usingProjectId = os.getenv('project_id', 'local')


def get_logging_level():
    return os.getenv("LOGGING_LEVEL", "INFO")


def configure_logging():
    logging_level = get_logging_level().upper()
    numeric_level = getattr(logging, logging_level, None)

    if not isinstance(numeric_level, int):
        raise Exception(f"Invalid log level: {numeric_level}")

    logging.basicConfig(
        level=numeric_level,
        datefmt="%Y-%m-%d %H:%M:%S",
        format="[%(asctime)s] [%(levelname)s] [%(module)s]: #%(funcName)s @%(lineno)d: %(message)s",
    )
    logging.info(f"Logging level: {logging_level}")


def read_config():
    if usingProjectId == "local":
        yaml_file_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        with open(yaml_file_path) as yaml_file:
            config = yaml.safe_load(yaml_file)
        return config
    else:
        backend_url = fetch_backend_url_firestore()
        backend_endpoint = f"{backend_url}/api/v1/execute_bot_signal"
        config = {
            'backend_endpoint': [backend_endpoint]
        }
        return config


configure_logging()
config = read_config()
