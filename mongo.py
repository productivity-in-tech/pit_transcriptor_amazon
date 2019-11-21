import pymongo
import os

client = pymongo.MongoClient(os.environ['MONGODB_HOST'], os.environ['MONGODB_PORT'])
db = client[os.environ['MONGODB_DB']]
transcriptions = db['transcriptions']
