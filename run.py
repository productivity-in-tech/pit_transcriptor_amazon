import tempfile
import bcrypt
import boto3
import os
import responder
import requests
import transcriber
import logging

logging.basicConfig(level=logging.WARNING)
# Amazon Information
bucket= os.environ['BUCKET_NAME']
storage = boto3.client('s3',)
transcribe = boto3.client('transcribe')

def check_for_jobs(req, transcribe): 
	email = req.params.get('email')
	
	if email:
		return transcribe.list_transcription_jobs(JobNameContains=email)
	
	

api = responder.API()

@api.route('/')
class Index:

    def on_get(self, req, resp):
		jobs = check_for_jobs(transcribe, req)
	    resp.html = api.template('index.html', jobs=jobs)

    async def on_post(self, req, resp,):
        @api.background.task
        def upload_file(data, filename, key, email):
            with tempfile.TemporaryFile() as temp_file:
                temp_file.write(data['audio_file']['content'])
                temp_file.seek(0)
                storage.upload_fileobj(
                        temp_file,
                        Bucket=bucket,
                        Key=data['email']+key,
                        )
                        
            email_upload_update()
            transcriber.start_transcription(
                    storage=storage,
                    transcribe=transcribe,
                    bucket=bucket,
                    key=key,
                    ChannelIdentification=False,
                    lang='en-US',
                    )

        data = await req.media(format='files')
        filename = data['audio_file']['filename']
        logging.debug(data['audio_file']['content'])
        key = data['email'] + transcriber.get_key(filename)


        upload_file(data, filename=filename, key=key)
        upload_message = f'{filename} has been uploaded and queued for \
                transcription'
		jobs = check_for_jobs(transcribe, req)        	
        resp.html = api.template('index.html', jobs=jobs, message=upload_message)


api.run()
