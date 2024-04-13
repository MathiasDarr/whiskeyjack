""" Flask App """

import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from config import get_configuration, configure
from flask import Flask

from whiskeyjack_upload.views import mount_app_blueprints

BINDMOUNT_DIR = '/usr/src/app/appdata'


def create_app(docker):
    app = Flask(__name__)  # name for the Flask app (refer to output)
    mount_app_blueprints(app)
    setup_logging()

    app = Flask(__name__)  # name for the Flask app (refer to output)

    mount_app_blueprints(app)
    print(f"Configuration:-{docker}")
    # retrieve and set the configuration based on the environment, docker environment, and service
    configuration = get_configuration(docker)
    app.config.from_mapping(configuration)
    configure(app)
    return app


def setup_logging():
    logFormatter = logging.Formatter(
        "%(asctime)s [%(filename)s:%(lineno)s - %(funcName)20s()] [%(levelname)-4.7s]  %(message)s"
    )

    log = logging.getLogger("werkzeug")
    log.setLevel(logging.DEBUG)
    log.propagate = False

    if len(log.handlers) < 1:
        streamHandler = logging.StreamHandler(sys.stdout)
        streamHandler.setFormatter(logFormatter)
        log.addHandler(streamHandler)
    else:
        streamHandler = log.handlers[0]
        streamHandler.setFormatter(logFormatter)

    os.makedirs("logs", exist_ok=True)

    fileHandler = RotatingFileHandler("logs/app.log", maxBytes=500000)
    fileHandler.setFormatter(logFormatter)
    log.addHandler(fileHandler)
