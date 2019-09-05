from tempfile import TemporaryFile
import boto3
import os
import responder
import transcriber
import logging

logging.basicConfig(level=logging.INFO)
# Amazon Information
bucket= os.environ['BUCKET_NAME']
storage = boto3.client('s3',)
transcribe = boto3.client('transcribe')

api = responder.API()

@api.route('/')
class Index:

    def on_get(self, req, resp):
        resp.html = api.template('index.html')

    async def on_post(self, req, resp,):
        @api.background.task
        def upload_file(data, filename, key):
            with TemporaryFile() as temp_file:
                temp_file.write(data['audio_file']['content'])
                storage.upload_fileobj(
                        temp_file,
                        Bucket=bucket,
                        Key=key,
                        )
            transcription.start_transcription(
                    storage=storage,
                    transcribe=transcribe,
                    bucket=bucket,
                    key=key,
                    ChannelIdentification=False,
                    lang='en_US',
                    )

        data = await req.media(format='files')
        filename = data['audio_file']['filename']
        logging.debug(data['audio_file']['content'])
        logging.info(f'{filename} uploaded')
        key = transcriber.make_key(filename)

        upload_file(data, filename=filename, key=key)
        upload_message = f'{filename} has been uploaded and queued for \
                transcription'
        resp.html = api.template('index.html', message=upload_message)
api.run()
