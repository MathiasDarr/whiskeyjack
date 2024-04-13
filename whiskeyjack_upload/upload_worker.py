import logging
import traceback
import boto3
import os
log = logging.getLogger('werkzeug')

s3 = boto3.resource('s3')

def upload_file_to_s3(file: str, key_prefix: str, delete_local=True) -> str:
    """
    Upload a local file to S3
    :param file: full path of local file
    :param key_prefix: s3 key prefix
    :return: full s3 key of the saved file
    """
    data_key = f"{key_prefix}/{os.path.basename(file)}"
    BUCKET = "bard-api-sub-dominant"
    s3.meta.client.upload_file(file, BUCKET, data_key)
    return f"s3://{BUCKET}/{data_key}"


def upload(filepath):
    log.info("dafdaf")
    try:
        prefix = "data/raw-data/ephemeral"
        upload_file_to_s3(file=filepath, key_prefix=prefix)
        log.debug(f"Uploaded file {filepath.split('/')[-1]} to s3")

    except Exception as e:
        log.error(f"{e}: {traceback.format_exc()}")

