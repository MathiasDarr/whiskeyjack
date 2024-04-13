from os import environ
from pprint import pprint

from flask import Flask

class BaseConfig:
    REDIS_HOST = "redis.ephemeral-development"
    FLASK_ENV="development"

class Local:
    REDIS_HOST = "redis"

class ECS:
    pass

def get_configuration(docker):
    """Helper function to retrieve configuration based on environment cross product."""
    dockerenvs = dict(local=Local, ecs=ECS)
    dockerenv_config = dockerenvs[docker]

    config = {
        **BaseConfig.__dict__,
        **dockerenv_config.__dict__,
    }
    config["DOCKER"] = docker
    pprint(config, indent=4)
    return config


def configure(app: Flask):
    """Setup environment based on the app.

    Args:
        app (Flask): current Flask application.
    """
    app.config["ENV"] = app.config["FLASK_ENV"]
    environ["FLASK_ENV"] = app.config["FLASK_ENV"]


