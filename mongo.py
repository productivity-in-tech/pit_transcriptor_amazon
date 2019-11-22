import pymongo
import os

client = pymongo.MongoClient(os.environ['MONGODB_URI'])
db = pymongo.get_default_database()
transcription_collection = db['transcriptions']
