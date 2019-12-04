from datetime import datetime
import arrow
import re
import logging
import math
import os
import time
from pathlib import Path

import json_builder
import mongo
import responder
import s3
import transcriber
import wtforms.fields as fields
import wtforms.validators as validators
from flask import Flask, flash, render_template, request, session
from flask_wtf import FlaskForm
from forms.forms import SetupForm, UploadForm
from werkzeug.utils import secure_filename

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

@app.route('/transcription/<key>', methods=['GET', 'POST'])
def get_transcription_page(key):
    version_date =  datetime.utcnow().strftime('%Y%m%d%H%M%S')
    flags = transcriber.flags

    if request.method == 'POST':
        transcription_text = request.form['transcription']
        transcriptions = mongo.transcription_collection.find_one_and_update(
                {'key': key}, 
                {'$set':
                    {f"transcriptions.{version_date}": transcription_text},
                })
        job = post['job']


    if request.method == 'GET':
        transcript = mongo.transcription_collection.find_one(
                {'key': key, 'transcriptions': {'$exists': True}}
        )

        if not transcript:
            job = transcriber.transcribe.get_transcription_job(TranscriptionJobName=key)
            logging.debug(job)
            transcription = transcriber.get_transcription(job)
            transcription_text = json_builder.build_transcript(transcription)
            transcript = {version_date: transcription_text}
            transcriptions = mongo.transcription_collection.insert_one(
                    {
                        'key': key,
                        'job': job,
                        'transcriptions': transcript,
                    })

    transcriptions = sorted(transcript['transcriptions'].items(), key=lambda x:x[0])
    version_date, transcription_text = transcriptions[-1]
    job = transcript['job']


    if len(transcriptions) > 1:
        previous_version = transcriptions[-2][-1]
        diff = unified_diff(previous_version, transcription_text)


    class EditTranscriptionForm(FlaskForm):
        transcription = fields.TextAreaField('Transcription', default=transcription_text)
        update_version = fields.HiddenField('Update_Version', default=version_date)
        submit = fields.SubmitField('Submit Changes')

    return render_template(
                'transcript.html',
                flags=flags,
                job=job,
                version_date = arrow.get(version_date, 'YYYYMMDDHHmmss').format('DD MMM, YYYY HH:ss'),
                form = EditTranscriptionForm(),
                count = len(re.findall(r'\*.*\*', transcription_text)),
                diff = diff,
        )


if __name__ == "__main__":
    app.run(debug=True, threaded=True, port=5000)
