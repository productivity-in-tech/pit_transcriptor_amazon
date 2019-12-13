import os
from dotenv import load_dotenv
from datetime import datetime
import difflib
import arrow
import re
import logging
import math
import time
from pathlib import Path

import pymongo
import mongo
import s3
import transcriber
from wtforms.fields import html5
import wtforms.fields as fields
import wtforms.validators as validators
from flask import (
        Flask,
        flash,
        render_template,
        request,
        session,
        Markup,
        redirect,
        url_for,
        )
from flask_wtf import FlaskForm
from forms.forms import (
        SetupForm,
        UploadForm,
        )

logging.basicConfig(level=logging.WARNING)

load_dotenv()

app = Flask(__name__)
app.secret_key = 'This is a test'

@app.route("/")
def index():
    form = UploadForm()
    recent_uploads = mongo.transcription_collection.find(
            sort = [('job.CreationTime', pymongo.DESCENDING)],
            limit = 5,
            )
    return render_template(
            "index.html",
            form=form,
            recent_uploads=recent_uploads)

@app.route("/upload-file", methods=["POST"])
def upload_file():
    email = request.form.get('email')
    audio_file = request.files['audio_file']
    filename = Path(audio_file.filename)
    key = s3.get_key(filename)
    s3.upload_audio_file(fileobj=audio_file, key=key)

    return redirect(url_for('setup_transcription_page', key=key))

@app.route("/setup-transcription/<key>")
def setup_transcription_page(key):
    """Add more information to the transcription"""

    class UpdatedSetupForm(SetupForm):
        if not session.get('project_key') == key:
            session['project_key'] = key

        project_name = fields.StringField(
            "Project Name",
            default=session.get('project_key', key),
            filters=[lambda x:x.title()],
            validators=[validators.InputRequired()],
        )

        email = html5.EmailField(
                "email",
                validators=[validators.InputRequired()],
                default=request.form.get('email', ''),
                )

    form = UpdatedSetupForm()


    return render_template("setup.html", form=form)


@app.route("/verify-setup", methods=["POST"])
def confirm_transcription():
    form = SetupForm()
    return render_template("verify_setup.html", form=form)


@app.route("/start-transcription", methods=["POST"])
def start_transcription():
    language = request.form["language"]
    job_name = re.sub(r'[^0-9a-zA-Z]+', '-', request.form['project_name'])
    channel_identification = request.form.get("channel_identification")
    max_speaker_labels = int(request.form['max_speakers'])

    if max_speaker_labels and not channel_identification:
        show_speaker_labels = True

    else:
        show_speaker_labels = False

    transcriber.start_transcription(
        job_name = job_name,
        language = language,
        key = session['project_key'],
        channel_identification = channel_identification,
        max_speaker_labels = max_speaker_labels,
        show_speaker_labels = show_speaker_labels,
    )

    return redirect(url_for('get_transcription_page', key=job_name))

@app.route('/post-transcription', methods=['POST'])
def post_transcription_edit():
    version_date =  datetime.utcnow().strftime('%Y%m%d%H%M%S')
    key = request.form['job_name']
    transcription_text = request.form['transcription'].strip()
    transcriptions = mongo.transcription_collection.find_one_and_update(
            {'key': key},
            {'$set':
                {f"transcriptions.{version_date}": transcription_text},
            })
    return redirect(url_for('get_transcription_page', key=key))


@app.route('/search-replace', methods=['POST'])
def search_and_replace():
    version_date =  datetime.utcnow().strftime('%Y%m%d%H%M%S')
    key = request.form['job_name']
    job = mongo.transcription_collection.find_one({'key': key})
    transcription_text = re.sub(
        request.form['search_phrase'],
        request.form['replace_phrase'],
        job['transcriptions'][request.form['update_version']],
        flags=re.IGNORECASE)
    transcriptions = mongo.transcription_collection.find_one_and_update(
            {'key': key},
            {'$set':
                {f"transcriptions.{version_date}": transcription_text},
            })

    return redirect(url_for('get_transcription_page', key=key))


@app.route('/transcription/<key>')
def get_transcription_page(key,):
    transcript = mongo.transcription_collection.find_one(
            {'key': key, 'transcriptions': {'$exists': True}}
    )

    if not transcript:
        version_date =  datetime.utcnow().strftime('%Y%m%d%H%M%S')
        transcribe = transcriber.transcribe
        job = transcribe.get_transcription_job(TranscriptionJobName=key)

        if (status := transcriber.check(job)) != 'COMPLETED':
            return f'<h1>Current Status for {key}</h1><h2>{status=}</h2>'

        job_settings = job['TranscriptionJob']['Settings']
        show_speaker_labels = job_settings['ShowSpeakerLabels']
        channel_identification = job_settings['ChannelIdentification']

        if show_speaker_labels and not channel_identification:
            transcription_text = transcriber.format_speaker_transcription(job)
            transcript = {version_date: transcription_text}
            transcriptions = {
                        'key': key,
                        'job': job,
                        'transcriptions': transcript,
                    }
            mongo.transcription_collection.insert_one(transcriptions)

    transcriptions = sorted(transcript['transcriptions'].items(), key=lambda x:x[0])
    version_date, transcription_text = transcriptions[-1]
    job = transcript['job']

    class EditTranscriptionForm(FlaskForm):
        transcription = fields.TextAreaField('Transcription', default=transcription_text)
        job_name = fields.HiddenField('Transcription_Job_Name', default=key)
        update_version = fields.HiddenField('Update_Version', default=version_date)
        submit = fields.SubmitField('Save Changes')

    class SearchandReplaceForm(FlaskForm):
        update_version = fields.HiddenField('Update_Version', default=version_date)
        job_name = fields.HiddenField('Transcription_Job_Name', default=key)
        search_phrase = fields.StringField('Replace All')
        replace_phrase = fields.StringField('Replace With')
        submit = fields.SubmitField('Find/Replace')

    return render_template(
                'transcript.html',
                flags=transcriber.flags,
                job=job,
                version_date = arrow.get(version_date, 'YYYYMMDDHHmmss').format('DD MMM, YYYY HH:ss'),
                form = EditTranscriptionForm(),
                search_form = SearchandReplaceForm(),
                issue_count = len(re.findall(r'\*.*\*', transcription_text)),
                version_count = len(transcriptions),
        )


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, threaded=True)
