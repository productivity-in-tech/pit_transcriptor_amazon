from pathlib import Path
import boto3
import click
import json
import logging
import os
import requests
import shutil
import sys
import time
import typing


# Pushover Information
pushover_url = 'https://api.pushover.net/1/messages/.json'
pushover_data = {
        'app_token': os.environ['PUSHOVER_APP_TOKEN'],
        'user_key': os.environ['PUSHOVER_USER_KEY'],
        }

    return upload


def start_transcription(
        *,
        storage=storage,
        transcribe=transcribe,
        bucket=bucket,
        key=key,
        ChannelIdentification=True
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





@click.command()
@click.option('--notifications', '-n', is_flag=True)
@click.option('--channels', type=Click.choice([1, 2]), default=1)
@click.option('--check', '-c', is_flag=True)
@click.argument('base_audio_file')
def _main(
        notifications,
        channels,
        base_audio_file,
        skip_upload,
        ):

    # Amazon Information
    bucket= os.environ['BUCKET_NAME']
    storage = boto3.client('s3')
    transcribe = boto3.client('transcribe')
    key=Path(base_audio_file).name.replace(' ', '')

    if check:
        """Calling check skips the transcription starting point
and just checks the status for the file"""
        job = transcribe.get_transcription_job(TranscriptionJobName=key)
        job_status = job['TranscriptionJob']['TranscriptionJobStatus']

        if job_status == 'IN PROGRESS':
            print(f'Job {key} still in progress. Try again later.')

        else:
            job_uri = job['TranscriptionJob']['Transcript']['TranscriptFileUri']
            r = requests.get(job_uri)
            r.raise_for_status()

            with open(f'{key}.json', 'w') as json_file:
                json_file.write(json.dumps(r.json()))
            print('Job: {key} complete and written')

        return # Terminates the script

    storage.upload_file(
                Filename=base_audio_file,
                Bucket=bucket,
                Key=key,
                )

    if notification:
        pushover_data['message'] = 'File Uploaded. Beginning transcription'
        pushover_data['title'] = 'file uploaded'
        r = requests.post(pushover_url, data=pushover_data)
        r.raise_for_status

    channel_count = {1: False, 2: True}
    return start_transcription(ChannelIdentification=channel_count[channels])


if __name__ == '__main__':
    _main()
