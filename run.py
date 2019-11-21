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
import mutagen
import requests
import responder
import s3
import transcriber
from faker import Faker

logging.basicConfig(level=logging.WARNING)
fake = Faker()
api = responder.API()


@api.route("/")
def index(req, resp):
    resp.html = api.template("index.html")


@api.route("/setup-transcription")
async def setup_transcription(req, resp):
    transcription_cost = 8
    data = await req.media(format="files")


@api.route("/submit")
async def post_submit(req, resp):
    if not "audio_file" in data:
        key = req.params["key"]
        email = req.params["email"]
        job = start_transcription(key)
        insert = {"$set", {f"transcriptions.{key}.job": job}}
        collection.find_one_and_update({"email": email}, insert)
        sendgrid.email
        resp.html = api.template(
            "transcription_still_uploading.html", key_url=f"/transcriptions/{key}"
        )

    else:
        logging.warning("No Audio File Detected")
        resp.html("index.html")


@api.route("/transcriptions/{key}")
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

    resp.html = api.template(
        "transcript.html",
        job=job,
        flags=transcriber.flags,
        status=status,
        transcript=transcript,
    )
