from pathlib import Path
import logging
import math
import os
import time

import maya

import celery_tasker
import json_builder
import mongo
import responder
import s3
import transcriber
from flask import (
        Flask,
        flash,
        render_template,
        request,
        session,
        )
from forms.forms import SetupForm, UploadForm
from werkzeug.utils import secure_filename
import wtforms.fields as fields
import wtforms.validators as validators

logging.basicConfig(level=logging.WARNING)

app = Flask(__name__)
app.secret_key = "This is a test"


@app.route("/")
def index():
    """ Go to the homepage. On Submit Upload the file to s3, create celery task and and set billing price."""
    form = UploadForm()
    return render_template("index.html", form=form)


@app.route("/setup-transcription", methods=["POST"])
def setup_transcription_page():
    """Add more information to the transcription"""

    filename = Path(request.files['audio_file'].filename)

    class UpdatedSetupForm(SetupForm):
        project_name = fields.StringField(
            "Project Name",
            default=filename.stem,
            filters=[lambda x:x.title()],
            validators=[validators.InputRequired()],
        )

    form = UpdatedSetupForm()

    session['key'] = s3.get_key(filename)

    return render_template("setup.html", form=form)


@app.route("/verify-setup", methods=["POST"])
def confirm_transcription():
    form = SetupForm()
    return render_template("verify_setup.html", form=form)


@app.route("/start_transcription", methods=["POST"])
def start_transcription():
    language = request.form["language"]
    storage = request.form["storage"]
    transcribe = request.form["transcribe"]
    channel_identification = request.form["channel_identification"]
    job = transcriber.start_transcription(
        key=session['key'],
        language=language,
        storage=storage,
        transcribe=transcribe,
        channel_identification=channel_identification,
    )
    return url_for('get_transcription_page', key=key)

@app.route('/transcription/<key>')
def get_transcription_page(key):
    flags = transcriber.flags
    job = transcriber.get_job(key)['TranscriptionJob']
    transcript = json_builder.build_transcript(job)
    return render_template('transcript.html', flags=flags, job=job, transcription=channels,
    )


if __name__ == "__main__":
    app.run(debug=True, threaded=True, port=5000)
