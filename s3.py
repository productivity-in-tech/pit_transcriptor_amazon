"""
This is the Amazon S3 information from the project.
Any sensitive data is stored in the environment variables and not in this file.
"""
from dotenv import load_dotenv
import os
from pathlib import Path
import tempfile

from uuid import uuid4
import boto3


def upload_audio_file(key, fileobj):
    storage = boto3.client("s3")
    bucket = os.environ.get('BUCKET_NAME')
    return storage.upload_fileobj(fileobj, bucket, key)


def get_key(filename):
    return str(uuid4()) + filename.suffix
