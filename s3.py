"""
This is the Amazon S3 information from the project.
Any sensitive data is stored in the environment variables and not in this file.
"""
import os
from pathlib import Path
import tempfile

from uuid import uuid4
import boto3

bucket = os.environ.get("BUCKET_NAME", True)
storage = boto3.client("s3")

def download_audio_file(key, data):
    return storage.download_obj(bucket, key, data)

def upload_audio_file(key, data):
    return storage.upload_fileobj(data, Key=key, Bucket=bucket)

def get_key(filename):
    return str(uuid4()) + filename.extension
