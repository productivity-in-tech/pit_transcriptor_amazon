import json
import logging
import os
import shutil
import sys
import time
import typing
from pathlib import Path

import click

import boto3
import requests

# Amazon Information
bucket = os.environ.get("BUCKET_NAME", True)
storage = boto3.client("s3")
transcribe = boto3.client("transcribe")
flags = {
    'en-US': 'US English',
    'en-GB': 'British English',
    'es-US': 'US Spanish',
    'en-AU': 'Australian English',
    'fr-CA': 'Canadian Friend',
    'de-DE': 'German',
    'pt-BR': 'Brazilian Portuguese',
    'fr-FR': 'French',
    'it-IT': 'Italian',
    'ko-KR': 'Korean',
    'es-ES': 'Spanish',
    'en-IN': 'Indian English',
    'hi-IN': 'Indian Hindi',
    'ar-SA': 'Modern Standard Arabic',
    'ru-RU': 'Russian',
    'zh-CN': 'Mandarin Chinese',
    }

@click.command()
@click.argument("key")
@click.option("--language", "-l", default="en-US")
def start_transcription(
    key,
    *,
    language,
    storage=storage,
    transcribe=transcribe,
    bucket=bucket,
    channel_identification=True,
):
    transcribe_job_uri = f"{storage.meta.endpoint_url}/{bucket}/{key}"
    transcribe.start_transcription_job(
        TranscriptionJobName=key,
        Media={"MediaFileUri": transcribe_job_uri},
        MediaFormat=Path(key).suffix[1:],
        LanguageCode=language,
        Settings={"ChannelIdentification": channel_identification},
    )
    return key


def get_key(file_path):
    return Path(file_path).name.replace(" ", "")


def get_job(key, transcribe=transcribe):
    return transcribe.get_transcription_job(TranscriptionJobName=key)


def check(job):
    """Calling check skips the transcription starting point
and just checks the status for the file"""
    job_status = job["TranscriptionJob"]["TranscriptionJobStatus"]
    return job_status


def get_transcription(job):
    if check(job) == 'COMPLETE':
        job_uri = job["TranscriptionJob"]["TranscriptFileUri"]
        r = requests.get(job_uri)
        logging.debug(r.json())
        r.raise_for_status()
        return r.json()

    else:
        'Error Error'


if __name__ == "__main__":
    start_transcription()
