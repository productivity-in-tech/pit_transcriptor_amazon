import os

import pymongo

client = pymongo.MongoClient(os.environ["MONGODB_URI"])
db = client.get_default_database()
transcription_collection = db["transcriptions"]


def add_audio(email: str, key: str):
    return transcription_collection.find_one_and_update(
        {"email": email}, {"$push: {transcriptions: {key:{}}}"}, upsert=True
    )


def get_transcription_job(email: str, key: str):
    return transcription_collection.find_one({f'{email}.transcriptions': key})
