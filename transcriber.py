from pathlib import Path
import boto3
import json
import logging
import os
import requests
import shutil
import sys
import time
import typing


def start_transcription(
        *,
        storage,
        transcribe,
        bucket,
        key,
        ChannelIdentification=True,
        lang='en-US',
        ):
    transcribe_job_uri = f'{storage.meta.endpoint_url}/{bucket}/{key}'
    transcribe.start_transcription_job(
            TranscriptionJobName=key,
            Media={'MediaFileUri': transcribe_job_uri},
            MediaFormat= Path(key).suffix[1:],
            LanguageCode=lang,
            Settings={'ChannelIdentification': True},
            )
    return key

def get_key(file_path):
    return Path(file_path).name.replace(' ', '')

def get_job(transcribe, key):
    return transcribe.get_transcription_job(TranscriptionJobName=key)


def check(job):
    """Calling check skips the transcription starting point
and just checks the status for the file"""
    job_status = job['TranscriptionJob']['TranscriptionJobStatus']
    return job_status

def get_transcript(job):
    job_uri = job['Transcript']['TranscriptFileUri']
    r = requests.get(job_uri)
    logging.debug(r.json())
    r.raise_for_status()
    return r.json()