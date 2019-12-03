import os

import pymongo

client = pymongo.MongoClient(f'{os.environ.get("MONGODB_URI")}?retryWrites=false')
db = client.get_default_database()
transcription_collection = db["transcriptions"]


def add_transcription(key: str, transcription_text: str):
    return transcription_collection.find_one({'key': key})


def get_transcription_job(email: str, key: str):
    return transcription_collection.find_one({f'{email}.transcriptions': key})
