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
import time
import tempfile
import logging
import urllib.parse


logging.basicConfig(level=logging.WARNING)
fake = Faker()
api = responder.API()

# Amazon Information
bucket= os.environ.get('BUCKET_NAME', True)
storage = boto3.client('s3')
transcribe = boto3.client('transcribe')
stripe.api_key = os.environ['STRIPE_SECRET_KEY_TEST']
stripe_public_key = os.environ['STRIPE_PUBLIC_KEY_TEST']

def friendly_date(job):
    if 'CreationTime' in job:
        friendly_creation = maya.parse(job['CreationTime']).slang_time()
        job['CreationTime'] = friendly_creation

    if 'CompletionTime' in job:
        friendly_completion = maya.parse(job['CompletionTime']).slang_time()
        job['CompletionTime'] = friendly_completion

    return job

@api.background.task
def start_transcription(key):
    """replace with celery task to check transcription status"""
    all_objects = storage.list_objects_v2(
            Bucket=bucket,
            MaxKeys=1,
            Prefix=key,
            )

    while 'Contents' not in all_objects:
        time.sleep(30)
        all_objects = storage.list_objects_v2(
                Bucket=bucket,
                MaxKeys=1,
                Prefix=key,
                )

    transcriber.start_transcription(
        storage=storage,
        transcribe=transcribe,
        bucket=bucket,
        key=key,
        ChannelIdentification=False,
        lang='en-US',
        )

@api.route('/login')
def login(req, resp):
    resp.html('index.html')


@api.route('/')
def index(req, resp):
    resp.html = api.template('index.html')


@api.route('/setup-transcription')
async def setup_transcription(req, resp):
    transcription_cost = 8
    data = await req.media(format='files')

    if not 'audio_file' in data:
        logging.warning('No Audio File Detected')
        resp.html('index.html')
        return

    with tempfile.TemporaryFile() as temp_file:
        temp_file.write(data['audio_file']['content'])
        temp_file.seek(0)
        length = mutagen.File(temp_file).info.length
        minutes = math.ceil(length/60)
        logging.warning(f'length - {minutes} minutes')


    filename = data['audio_file']['filename']
    key = '-'.join(fake.words(nb=4, unique=False)) + Path(filename).suffix
    line_item = {
            'name': 'PIT-transcription',
            'description': f'Transcription: {filename}-{key}',
            'amount': transcription_cost,
            'currency': 'usd',
            'quantity': minutes,
            }

    session = stripe.checkout.Session.create(
            cancel_url = os.environ['URL_ROOT'] + '/cancel',
            success_url = '{}{}{}'.format(
                    os.environ['URL_ROOT'],
                    '/submit?checkout_id={CHECKOUT_SESSION_ID}&key=',
                    key,
                    ),
            payment_method_types = ['card'],
            line_items = [line_item],
            )

    logging.info(session)

    @api.background.task
    def upload_file(data, key, filename):
        """TODO: REPLACE WITH CELERY TASK TO UPLOAD FILE"""
        with tempfile.TemporaryFile() as temp_file:
            temp_file.write(data['audio_file']['content'])
            temp_file.seek(0)
            storage.upload_fileobj(
                    temp_file,
                    Key=key,
                    Bucket=bucket,
                    ExtraArgs={
                        'Metadata': {
                                'filename': filename,
                                },
                        },
                    )

    upload_file(data, key=key, filename=filename)
    resp.headers['key'] = key
    resp.html = api.template(
            'get_transcription_settings.html',
            filename=filename,
            session_id=session['id'],
            cost='{:,.2f}'.format(.01 * transcription_cost * minutes),
            stripe_public_key=stripe_public_key,
            )

@api.route('/submit')
async def post_submit(req, resp):
    key = req.params['key']
    start_transcription(key)
    resp.html = api.template(
        'transcription_still_uploading.html',
        key_url=f'/transcriptions/{key}',
        )

@api.route('/transcriptions/{job_name}')
def get_transcription_page(req, resp, *, job_name):
    if 'Contents' in storage.list_objects_v2(
                Bucket=bucket,
                MaxKeys=1,
                Prefix=key,
                ):
            job = transcribe.get_transcription_job(TranscriptionJobName=job_name) \
                ['TranscriptionJob']

            status = job['TranscriptionJobStatus']
            job = friendly_date(job)

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

            resp.html = api.template(
                    'transcript.html',
                    job=job,
                    flags=flags,
                    transcript = transcript,
                    status = status,
                    )

    else:
        resp.html = api.template(
                'transcript_still_uploading.html',
                job_name=job_name,
                )


@api.route('/transcriptionUpdate')
async def transcription_update(req, resp):
    d = await req.media()
    print(d)

api.run()
