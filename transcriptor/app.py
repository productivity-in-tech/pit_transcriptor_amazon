from chalice import Chalice

import boto3
import json
import maya
import os
import requests
import tempfile


app = Chalice(app_name='transcriptor')

# Amazon Information
bucket= os.environ.get('BUCKET_NAME', True)
storage = boto3.client('s3')
transcribe = boto3.client('transcribe')


@app.route('/upload', methods=['POST'])
def upload_file():
    req = app.current_request
    key=req['key']

    # Save audio to temporary file and upload to s3
    with tempfile.TemporaryFile() as temp_file:
        temp_file.write(req['audio_file']['content'])
        temp_file.seek(0)
        storage.upload_fileobj(
                temp_file,
                Bucket=bucket,
                Key=key,
                )

    # Start Amazon Transcription
    transcribe_job_uri = f'{storage.meta.endpoint_url}/{bucket}/{key}'
    response = transcribe.start_transcription_job(
            TranscriptionJobName=key,
            LanguageCode=req['language_code'],
            Media={'MediaFileUri': transcribe_job_uri},
            Settings={'ChannelIdentification': req['ChannelIdentification']},
            )

    return response
