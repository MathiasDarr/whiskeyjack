from logging import getLogger
from rq import Queue
from rq.registry import FailedJobRegistry
from rq.job import Job

from whiskeyjack_upload.worker.redis_conn import RedisConn

_LOGGER = getLogger("werkzeug")

class RqManager:
    UploadQUEUE = None
    QUEUE = None
    FAILREGISTRY= FailedJobRegistry
    FAILUPLOADREGISTRY = FailedJobRegistry
    TASK_TIMEOUT = 3600  # 1 hour

    @staticmethod
    def initialize():
        try:
            redisConn = RedisConn.get_connection()
            RqManager.QUEUE = Queue(connection=redisConn)
            RqManager.UploadQUEUE = Queue('upload_queue', connection=redisConn)
            RqManager.FAILREGISTRY = FailedJobRegistry(
                connection=redisConn, queue=RqManager.QUEUE
            )
            _LOGGER.debug(f"REDIS_QUEUE_INIT {len(RqManager.QUEUE)}")
        except Exception as ex:
            _LOGGER.error(
                "ERROR: Cannot establish connection to Redis: %s", ex
            )
            raise ex from ex

    @staticmethod
    def enqueue(function, kwargs, maxretry=3, queue:str ='default'):
        if not RqManager.UploadQUEUE or not RqManager.QUEUE:
            RqManager.initialize()

        if queue == 'default':
            rq_queue = RqManager.QUEUE
        elif queue == 'upload':
            rq_queue = RqManager.UploadQUEUE
        else:
            raise Exception("No queue provided")

        try:
            rq_queue.enqueue(
                function,
                kwargs=kwargs,
                job_timeout=RqManager.TASK_TIMEOUT,
                # Retry up to 3 times, with longer interval in between retries
                # retry=Retry(max=maxretry, interval=[10, 30, 60]),
                on_failure=RqManager.report_failure,
            )
            _LOGGER.debug("REDIS_QUEUE_LENGTH %s", len(RqManager.QUEUE))
        except Exception as ex:
            _LOGGER.error(
                "ERROR: Cannot enqueue function call with RQ: %s", ex
            )
            raise ex from ex

    @staticmethod
    def get_failed_jobs():
        # get all failed job IDs and the exceptions they caused during runtime
        if not RqManager.FAILREGISTRY:
            RqManager.initialize()

        failedJobs = []
        for jobId in RqManager.FAILREGISTRY.get_job_ids():
            job = Job.fetch(jobId, connection=RedisConn.get_connection())
            failedJobs.append((jobId, job.exc_info))

        return failedJobs

    @staticmethod
    def report_failure(job, connection, type, value, traceback):
        _LOGGER.error(
            "ERROR: RQ job %s failed. Type: %s | Value: %s | Traceback: %s",
            job,
            type,
            value,
            traceback,
        )