import json
import logging
import math
import os
import tempfile
import time
import urllib.parse
from pathlib import Path
from uuid import uuid4

import maya

import celery_tasker
import json_builder
import mongo
import responder
import s3
import transcriber
from flask import Flask, flash, render_template, request
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms.fields.html5 import EmailField
from wtforms.fields import FileField
import wtforms.validators
from werkzeug.utils import secure_filename

logging.basicConfig(level=logging.WARNING)

app = Flask(__name__)
app.secret_key = "This is a test"

class UploadForm(FlaskForm):
    email = EmailField('email', [wtforms.validators.InputRequired()])
    audio_file = description= FileField('Audio File', [FileRequired]) 

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        email = request.form.get("email")
        data = request.files.get("audio_file")

        if not email:
            flash("Please Enter your email to Continue", "error")

        if not data:
            flash("Please Enter a file to Continue", "error")

        if email and data:
            key = s3.get_key(data)
            # s3.upload_audio_file(key, data)
            # mongo.add_audio(email, key, language)
            flash(f"{data.filename} transcription started")

        return render_template("setup.html", email=email, key=key)

    if request.method == "GET":
        form = UploadForm()
        return render_template("index.html", form=form)


@app.route("/setup-transcription/{key}", methods=["GET", "POST"])
def setup_transcription_page(*, key: str):
    email = request.headers.get("email")
    job = mongo.get_transcription_job(email, key)
    return render_template("setup.html") 


@app.route("/transcription/{key}", methods=["GET", "POST"])
def get_transcription_page(*, key: str):
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
