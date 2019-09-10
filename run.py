from faker import Faker
from pathlib import Path
from sendgrid import SendGridAPIClient

import transcriber
import boto3
import json
import math
import maya
import mutagen
import os
import responder
import requests
import stripe
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
    if 'CreationTime' in job:
        friendly_creation = maya.parse(job['CreationTime']).slang_time()
        job['CreationTime'] = friendly_creation

    if 'CompletionTime' in job:
        friendly_completion = maya.parse(job['CompletionTime']).slang_time()
        job['CompletionTime'] = friendly_completion

    return job


api = responder.API()

@api.route('/')
def index(req, resp):
        resp.html = api.template('index.html')


@api.route('/setup-transcription')
async def setup_transcription(req, resp):

    data = await req.media(format='files')
    logging.debug(data['audio_file']['filename'])

    with tempfile.TemporaryFile() as temp_file:
        temp_file.write(data['audio_file']['content'])
        temp_file.seek(0)
        length = mutagen.File(temp_file).info.length

    minutes = math.ceil(length/60)

    logging.debug(f'length - {minutes} minutes')

    stripe.api_key = os.environ['STRIPE_API_TOKEN']

    logging.debug(stripe.api_key)

    session = stripe.checkout.Session.create(
            cancel_url = os.environ['URL_ROOT'] + '/cancel',
            success_url = os.environ['URL_ROOT'] + '/submit',
            payment_method_types = ['card'],
            line_items = [
                    {
                        'name': 'PIT-transcription',
                        'description': 'PIT Transcription Services from Productivity in Tech',
                        'amount': 5,
                        'currency': 'usd',
                        'quantity': minutes,
                    }
                ],
            )
    filename = data['audio_file']['filename']
    resp.html = api.template(
            'get_transcription_settings.html',
            filename=filename,
            session_id=session['id'],
            stripe_public_key=os.environ['STRIPE_PUBLIC_KEY'],
            cost= '{:,.2f}'.format(.05 * minutes),
            )

@api.route('/submit')
async def post_submit(req, resp):
    @api.background.task
    def upload_file(data, key):
        with tempfile.TemporaryFile() as temp_file:
            temp_file.write(data['audio_file']['content'])
            temp_file.seek(0)
            storage.upload_fileobj(
                    temp_file,
                    Bucket=bucket,
                    Key=key,
                    )

        transcriber.start_transcription(
                storage=storage,
                transcribe=transcribe,
                bucket=bucket,
                key=key,
                ChannelIdentification=False,
                lang='en-US',
                )

    upload_file(data, key=key)
    resp.html = api.template(
            'index.html',
            message=upload_message,
            filename=filename,
            job_name=key,
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
    try:
        job = transcribe.get_transcription_job(TranscriptionJobName=job_name) \
                ['TranscriptionJob']
        status = job['TranscriptionJobStatus']

    except:
        status = 'Uploading to S3'

    if status == 'Uploading to S3':
        resp.html = api.template(
                'transcript_still_uploading.html',
                job_name=job_name,
                )
    else:
        job = friendly_date(job)
        transcript = transcriber.get_transcript(job)
        resp.html = api.template(
                'transcript.html',
                job=job,
                flags=flags,
                transcript = transcript,
                )


api.run()
