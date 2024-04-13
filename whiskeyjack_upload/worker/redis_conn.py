from redis import Redis
import logging
from flask import current_app

log = logging.getLogger('werkzeug')

class RedisConn():
    CONN = None

    @staticmethod
    def get_connection():
        if not RedisConn.CONN:
            try:
                log.info(f"THE REDIS HOST IS {current_app.config.get('REDIS_HOST')}")
                RedisConn.CONN = Redis(
                    host=current_app.config.get("REDIS_HOST"),
                    port=6379
                )
            except Exception as ex:
                log.error('Could not establish connection to Redis: {}'.format(ex))
                raise ex
        
        return RedisConn.CONN