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
    job_name,
    *,
    key,
    language,
    channel_identification,
    show_speaker_labels,
    max_speaker_labels: int=0,
    storage=storage,
    transcribe=transcribe,
    bucket=bucket,
):
    settings={
        "ChannelIdentification": channel_identification,
        "ShowSpeakerLabels": True,
        },

    if channel_identification:
        settings['show_speaker_labels'] = False
        settings['max_speaker_labels'] = 0

    elif show_speaker_labels and max_speaker_labels > 1:
        settings['show_speaker_labels'] = show_speaker_labels
        settings['max_speaker_labels'] = max_speaker_labels


    transcribe_job_uri = f"{storage.meta.endpoint_url}/{bucket}/{key}"
    return transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={"MediaFileUri": transcribe_job_uri},
        MediaFormat=Path(key).suffix.lstrip('.'),
        LanguageCode=language,
        Settings=settings,
    )


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
    job_uri = job['TranscriptionJob']["Transcript"]["TranscriptFileUri"]
    r = requests.get(job_uri)
    logging.debug(r.json())
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    start_transcription()
