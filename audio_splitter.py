from pathlib import Path
import boto3
import json
import logging
import os
import requests
import shutil
import sys
import time

bucket= os.environ['BUCKET_NAME']
data = {
        'app_token': os.environ['PUSHOVER_APP_TOKEN'],
        'user_key': os.environ['PUSHOVER_USER_KEY'],
        }

base_audio_file = sys.argv[1]
storage = boto3.client('s3')
transcribe = boto3.client('transcribe')
key=Path(base_audio_file).name.replace(' ', '')

def upload_file(
        storage=storage,
        file_name=base_audio_file,
        data=data,
        key=key,
        bucket=bucket
        ):

    upload = storage.upload_file(
            Filename=base_audio_file,
            Bucket=bucket,
            Key=key,
            )
    data['message'] = f'''{key} has been successfully uploaded 
and transcription will begin'''
    data['title'] = 'Audio Uploaded, Beginning Transcription'
    requests.post('https://api.pushover.net/1/messages/.json', data=data)

def start_transcription(
        storage=storage,
        transcribe=transcribe,
        data=data,
        bucket=bucket,
        key=key,
        lang='en-US'):
    transcribe_job_uri = f'{storage.meta.endpoint_url}/{bucket}/{key}' 
    #transcribe.start_transcription_job(
#            TranscriptionJobName=key,
#            Media={'MediaFileUri': transcribe_job_uri},
#            MediaFormat= Path(key).suffix[1:],
#            LanguageCode=lang,
#            Settings={'ChannelIdentification': True},
#            )
    print('transcription started')
#    time.sleep(360)
    job = transcribe.get_transcription_job(TranscriptionJobName=key) 

    while job['TranscriptionJob']['TranscriptionJobStatus'] == 'IN_PROGRESS':
        time.sleep(60)
        job = transcribe.get_transcription_job(TranscriptionJobName=key) 

    data['message'] = f'{base_audio_file} has been successfully transcribed'
    data['title'] = 'Transcription Complete!'
    requests.post('https://api.pushover.net/1/messages/.json', data=data)
    r = requests.get(job['TranscriptionJob']['Transcript']['TranscriptFileUri'])
    r.raise_for_status()

    with open(f'{key}.json', 'w') as json_file:
        json_file.write(json.dumps(r.json()))

if __name__ == '__main__':
    #upload_file()
    start_transcription()
