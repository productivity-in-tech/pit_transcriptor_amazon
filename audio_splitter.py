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
def start_transcription(
        key,
        *,
        storage,
        transcribe,
        bucket,
        ChannelIdentification=True,
        lang='en-US',
        ):
    transcribe_job_uri = f'{storage.meta.endpoint_url}/{bucket}/{key}'
    click.echo(Path(key).suffix[1:])
    transcribe.start_transcription_job(
            TranscriptionJobName=key,
            Media={'MediaFileUri': transcribe_job_uri},
            MediaFormat= Path(key).suffix[1:],
            LanguageCode=lang,
            Settings={'ChannelIdentification': ChannelIdentification},
            )
    return key

@click.group()
def cli():
    pass


@cli.command()
@click.option('--channels', is_flag=True)
@click.option('--check', '-c', is_flag=True)
@click.argument('base_audio_file')
def transcription(
        channels,
        base_audio_file,
        check,
        directory,
        ):

    # Amazon Information
    bucket = os.environ['BUCKET_NAME']
    storage = boto3.client('s3')
    transcribe = boto3.client('transcribe')
    key=Path(base_audio_file).name.replace(' ', '')

    if check:
        job = transcribe.get_transcription_job(TranscriptionJobName=key)
        job_status = job['TranscriptionJob']['TranscriptionJobStatus']

        if job_status != 'IN_PROGRESS':
            job_uri = job['TranscriptionJob']['Transcript']['TranscriptFileUri']
            r = requests.get(job_uri)
            r.raise_for_status()

            with open(f'{key}.json', 'w') as json_file:
                json_file.write(json.dumps(r.json()))

            click.echo('Job: {key} complete and written')

        return # Terminates the script


    storage.upload_file(
            Filename=base_audio_file,
            Bucket=bucket,
            Key=key,
            )

    return start_transcription(
        key=key, bucket=bucket, storage=storage,
        transcribe=transcribe, ChannelIdentification=channels,
        )



@cli.command()
@click.argument('directory')
@click.option('--check', '-c', is_flag=True)
@click.option('--channels', is_flag=True)
@click.option('--file-format', default='mp3')
def bulk_transcription(
        directory,
        check,
        channels,
        file_format,
        ):

    bucket = os.environ['BUCKET_NAME']
    storage = boto3.client('s3')
    transcribe = boto3.client('transcribe')


    for path in Path(directory).rglob(f'*.{file_format}'):
        key = path.name.replace(' ', '')

        if check:
            job = transcribe.get_transcription_job(TranscriptionJobName=key)
            job_status = job['TranscriptionJob']['TranscriptionJobStatus']

            if job_status != 'IN_PROGRESS':
                job_uri = job['TranscriptionJob']['Transcript']['TranscriptFileUri']
                r = requests.get(job_uri)
                r.raise_for_status()

                with open(f'{key}.json', 'w') as json_file:
                    json_file.write(json.dumps(r.json()))

                click.echo(f'Job: {key} complete and written')

            continue # Terminates the script

        storage.upload_file(
                Filename=str(path),
                Bucket=bucket,
                Key=key,
                )

        start_transcription(
            key=key, bucket=bucket, storage=storage,
            transcribe=transcribe, ChannelIdentification=channels,
            )

    return

if __name__ == '__main__':
    cli()
