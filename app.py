import json
import logging
import math
import os
import tempfile
import time
import urllib.parse
from pathlib import Path

import maya

import celery_tasker
import json_builder
import responder
import s3
import transcriber
from faker import Faker
from flask import Flask, request, render_template


logging.basicConfig(level=logging.WARNING)
fake = Faker()

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        request.form['email']
        print(request.form) # email is contained in form
        print(request.files) # file data in request.files
        s3.upload_audio_file


    return render_template("index.html")


@app.route("/submit")
async def post_submit(req, resp):
    if not "audio_file" in data:
        key = req.params["key"]
        email = req.params["email"]
        job = start_transcription(key)
        insert = {"$set", {f"transcriptions.{key}.job": job}}
        collection.find_one_and_update({"email": email}, insert)
        sendgrid.email
        resp.html = app.template(
            "transcription_still_uploading.html", key_url=f"/transcriptions/{key}"
        )

    else:
        logging.warning("No Audio File Detected")
        resp.html("index.html")


@app.route("/transcriptions/{key}")
def get_transcription_page(req, resp, *, key):
    transcription = transcription_collection.find_one({"key": key})
    job = transcription["TranscriptionJob"]
    status = job["TranscriptionJobStatus"]
    job["CreationTime"] = maya.parse(job["CreationTime"]).slang_time()

    if job.get("CompletionTime"):  # If not yet complete there will be no data
        job["CompletionTime"] = maya.parse(job["CompletionTime"]).slang_time()

    if "versions" in transcription:  # Not written until the transcription is finished
        # TODO: Create Javascript Version of JSON Builder
        transcription_json = transcription["versions"][-1]
        transcript = json_builder.build_transcript(transcription_json)

    else:
        transcript = ""

    resp.html = app.template(
        "transcript.html",
        job=job,
        flags=transcriber.flags,
        status=status,
        transcript=transcript,
    )

if __name__ == "__main__":
    app.run(debug=True, threaded=True, port=5000)
