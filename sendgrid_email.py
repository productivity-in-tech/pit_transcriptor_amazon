import os
from pathlib import Path

from jinja2 import Template
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Content, To, From, Subject, HtmlContent, Mail

# Sendgrid Information
sg = SendGridAPIClient(api_key=os.environ["SENDGRID_API_KEY"])
from_email = "no_reply@transcriptor.productivitityintech.com"

def send_upload_email(to_email, filename, key, from_email=from_email):
    subject = Subject(f"{filename} - has been uploaded setup your transcription!")
    begin_transcript_template_path = "templates/email/transcription_begins.html"
    begin_transcript_email = Path(begin_transcript_template_path).read_text()
    template = Template(begin_transcript_email)
    content_text = template.render(
        URL_ROOT=os.environ["URL_ROOT"], filename=filename, key=key
    )
    content = HtmlContent(content_text)
    mail = Mail(
            from_email=From(from_email),
            subject=subject,
            to_emails=To(to_email),
            html_content=content)
    return sg.client.mail.send.post(request_body=mail.get())


def send_update_email(to_email, filename, key, from_email=from_email):
    subject = Subject(f"{filename} - has begun, transcription has begun!")
    begin_transcript_template_path = "templates/email/transcription_begins.html"
    begin_transcript_email = Path(begin_transcript_template_path).read_text()
    template = Template(begin_transcript_email)
    content_text = template.render(
        URL_ROOT=os.environ["URL_ROOT"], filename=filename, key=key
    )
    content = HtmlContent(content_text)
    mail = Mail(
            from_email=From(from_email),
            subject=subject,
            to_emails=To(to_email),
            html_content=content)
    return sg.client.mail.send.post(request_body=mail.get())
