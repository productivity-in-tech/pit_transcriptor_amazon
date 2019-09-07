import transcriber
import boto3
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

def friendly_date(job):
    friendly_creation = maya.parse(job['CreationTime']).slang_time()
    job['CreationTime'] = friendly_creation

    friendly_completion = maya.parse(job['CompletionTime']).slang_time()
    job['CompletionTime'] = friendly_completion
    return job

def check_for_jobs(email, transcribe=transcribe):
    if email:
        jobs = transcribe.list_transcription_jobs(JobNameContains=email)
        return map(friendly_date, jobs['TranscriptionJobSummaries'])

api = responder.API()

def escape_email(req):
    return req.params.get('email', '').replace('@', 'AT').replace('.', '_')


@api.route('/')
class Index:

    def on_get(self, req, resp):
        jobs = check_for_jobs(escape_email(req))
        logging.debug(jobs)
        resp.html = api.template('index.html', jobs=jobs)

    async def on_post(self, req, resp):
        @api.background.task
        def upload_file(data, filename, key):
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


        email = escape_email(req)
        data = await req.media(format='files')
        filename = data['audio_file']['filename']
        logging.debug(data['audio_file']['content'])
        key = email + transcriber.get_key(filename)


        upload_file(data, filename=filename, key=key)
        upload_message = f'{filename} has been uploaded and queued for \
                transcription'
        jobs = check_for_jobs(email)
        logging.warn(jobs)
        resp.html = api.template(
                'index.html',
                jobs=jobs,
                message=upload_message,
                )


@api.route('/transcript/{jobName}')
def get_transcript(req, resp, *, jobName):
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
    job = transcribe.get_transcription_job(jobName['TranscriptionJob'])
    job = friendly_date(job)
    resp.html = api.template('transcript.html', job=job, flags=flags)

api.run()
