from rq import Worker, Connection
import wsgi
import sys

from whiskeyjack_upload.worker.redis_conn import RedisConn

if __name__ == "__main__":
    app = wsgi.application
    app.app_context().push()

    if len(sys.argv) < 2:
        queue = "default"
    else:
        queue = sys.argv[1]

    redisConn = RedisConn.get_connection()
    with Connection(redisConn):
        worker = Worker(queue)
        worker.work(with_scheduler=True)

