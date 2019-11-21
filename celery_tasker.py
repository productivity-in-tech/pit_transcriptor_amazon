import mutagen
import tempfile
from s3 import storage
from sendgrid_email import send_update_email

def start_transcription(key, filename, language):
    """replace with celery task to check transcription status"""
    all_objects = storage.list_objects_v2(Bucket=bucket, MaxKeys=1, Prefix=key)

    while "Contents" not in all_objects:
        time.sleep(30)
        all_objects = storage.list_objects_v2(Bucket=bucket, MaxKeys=1, Prefix=key)

    job=transcriber.start_transcription(
        storage=storage,
        transcribe=transcribe,
        bucket=bucket,
        key=key,
        ChannelIdentification=False,
        lang=language,
    )

    return send_update_email(to_email, filename, key)

def get_file_length(key):
    with tempfile.TemporaryFile() as temp_file:
        download_audio_file(key, temp_file)
        length = mutagen.File(temp_file).info.length
        minutes = math.ceil(length / 60)

    line_item = {
        "name": "PIT-transcription",
        "description": f"Transcription: {filename}-{key}",
        "amount": transcription_cost,
        "currency": "usd",
        "quantity": minutes,
    }

