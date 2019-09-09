from faker import Faker
from pathlib import Path
from sendgrid import SendGridAPIClient

import transcriber
import boto3
import json
import maya
import os
import responder
import requests
import tempfile
import logging
import urllib.parse


logging.basicConfig(level=logging.WARNING)
# Amazon Information
bucket= os.environ['BUCKET_NAME']
storage = boto3.client('s3',)
transcribe = boto3.client('transcribe')

fake = Faker()

def friendly_date(job):
    friendly_creation = maya.parse(job['CreationTime']).slang_time()
    job['CreationTime'] = friendly_creation

    friendly_completion = maya.parse(job['CompletionTime']).slang_time()
    job['CompletionTime'] = friendly_completion
    return job


api = responder.API()

@api.route('/')
class Index:

    def on_get(self, req, resp):
        resp.html = api.template('index.html')

    async def on_post(self, req, resp):
        @api.background.task
        def upload_file(data, key):
            with tempfile.TemporaryFile() as temp_file:
                temp_file.write(data['audio_file']['content'])
                temp_file.seek(0)
                storage.upload_fileobj(
                        temp_file,
                        Bucket=bucket,
                        Key=('-').join(fake.words(nb=6, unique=False)),
                        )

            transcriber.start_transcription(
                    storage=storage,
                    transcribe=transcribe,
                    bucket=bucket,
                    key=key,
                    ChannelIdentification=False,
                    lang='en-US',
                    )

        data = await req.media(format='files')
        filename = Path(data['audio_file']['filename'])
        logging.debug(data['audio_file']['content'])
        logging.warning(f'filename - {filename.suffix}')
        key = '-'.join(fake.words(nb=6, unique=True)) + filename.suffix


        upload_file(data, key=key)
        upload_message = f'{filename} has been uploaded and queued for \
                transcription'
        resp.html = api.template(
                'index.html',
                message=upload_message,
                )


@api.route('/transcriptions/{job_name}')
def get_transcription_page(req, resp, *, job_name):
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
    job = transcribe.get_transcription_job(TranscriptionJobName=job_name)
    job = friendly_date(job['TranscriptionJob'])
    transcript = transcriber.get_transcript(job)
    resp.html = api.template(
            'transcript.html',
            job=job,
            flags=flags,
            transcript = transcript,
            )

api.run()
