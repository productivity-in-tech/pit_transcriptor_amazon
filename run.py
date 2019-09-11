from flask import Flask, render_template
from faker import Faker
from pathlib import Path
from sendgrid import SendGridAPIClient

import transcriber
import boto3
import celery
import json
import math
import maya
import mutagen
import os
import responder
import requests
import stripe
import time
import tempfile
import logging
import urllib.parse

app = Flask(__name__)

logging.basicConfig(level=logging.WARNING)
fake = Faker()


# Amazon Information
bucket= os.environ.get('BUCKET_NAME', True)
storage = boto3.client('s3')
transcribe = boto3.client('transcribe')
stripe.api_key = os.environ['STRIPE_SECRET_KEY_TEST']
stripe_public_key = os.environ['STRIPE_PUBLIC_KEY_TEST']

def friendly_date(job):
    if 'CreationTime' in job:
        friendly_creation = maya.parse(job['CreationTime']).slang_time()
        job['CreationTime'] = friendly_creation

    if 'CompletionTime' in job:
        friendly_completion = maya.parse(job['CompletionTime']).slang_time()
        job['CompletionTime'] = friendly_completion

    return job



@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run()
