"""
This is the Amazon S3 information from the project.
Any sensitive data is stored in the environment variables and not in this file.
"""
import os
from pathlib import Path
import tempfile

from uuid import uuid4
import boto3

storage = boto3.client("s3")

def upload_audio_file(key, file_type):
    bucket = os.environ.get('BUCKET_NAME'),
    presigned_post = storage.generate_presigned_post(
        Bucket = bucket,
        Key = key,
        Fields = {"acl": "public-read",
            "Content-Type": file_type},
        Conditions = [{"acl": "public-read",
            "Content-Type": file_type}],
        ExpiresIn = 3600,
        )

    print(presigned_post)

    return json.dumps({
        'data': presigned_post,
        'url': f'https://{bucket}.s3/amazonaws.com/{key}',
        })


def get_key(filename):
    return str(uuid4()) + filename.suffix
