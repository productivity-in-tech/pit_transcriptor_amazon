from celery import Celery
import boto3
import os

app = Celery('PIT-TRANSCRIPTOR')
app.conf.update(BROKER_URL=os.environ['REDIS_URL'],
                CELERY_RESULT_BACKEND=os.environ['REDIS_URL'])
bucket= os.environ['BUCKET_NAME']
storage = boto3.client('s3',)
transcribe = boto3.client('transcribe')


@app.task(default_retry_delay=30, retry_backoff=15, retry_backoff_max=180)
def check_for_upload(self, key):
    all_objects = storage.list_objects_v2(
            Bucket=bucket,
            MaxKeys=1,
            Prefix=key,
            )
    if 'Contents' not in all_objects:
        raise self.retry()

    else:


