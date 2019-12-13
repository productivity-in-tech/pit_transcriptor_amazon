from flask_wtf import FlaskForm
from pathlib import Path
import flask_wtf.file
import wtforms.fields.html5 as html5
import wtforms.fields as fields
import wtforms.validators as validators
import transcriber
from flask import request

class UploadForm(FlaskForm):
    audio_file = flask_wtf.file.FileField(
        "Audio File", [flask_wtf.file.FileRequired]
    )

    email = html5.EmailField(
        "Email",
        [validators.InputRequired()],
    )

class SetupForm(FlaskForm):
    email = html5.EmailField(
        "Email",
        [validators.InputRequired()],
    )

    project_name = fields.StringField(
        "Project Name",
        validators=[validators.InputRequired()],
        filters=[lambda x:x.title()]
    )

    language = fields.SelectField(
        "Language",
        choices=[(x, y) for x, y in transcriber.flags.items()],
    )

    channel_identification = fields.BooleanField(
        "Channel Identification",
    )

    max_speakers = fields.IntegerField(
        "Number of Speakers",
        _name="speakers",
        validators=[validators.Optional(), validators.NumberRange(2, 10)],
        description="Instructions AWS Transcribe to use speaker diarization and tells the algorithm how \
            many different speakers to detect. Will be ignored if Channel Identification is turned on.",
    )


