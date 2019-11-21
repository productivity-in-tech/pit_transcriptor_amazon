"""
This is the Amazon S3 information from the project.
Any sensitive data is stored in the environment variables and not in this file.
"""
import tempfile

import boto3

bucket = os.environ.get("BUCKET_NAME", True)
storage = boto3.client("s3")

def download_audio_file(key, data):
    return storage.download_obj(bucket, key, data)

def upload_audio_file(key):
    with tempfile.TemporaryFile() as temp_file:
        temp_file.write(data["audio_file"]["content"])
        temp_file.seek(0)

        storage.upload_fileobj(
            temp_file, Key=key, Bucket=bucket,
            )
