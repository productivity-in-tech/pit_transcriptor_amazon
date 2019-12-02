from jinja2 import Markup
from markdown import markdown
import datetime
import json
import logging
import re
import sys



def build_transcript(transcript_json):
    json_results = transcript_json['results']
    channels = json_results['channel_labels']['channels']

    voices = {'ch_0': 'speaker 1', 'ch_1': 'speaker 2'}
    speaker = voices['ch_0']
    text_lines = [f'{speaker}\n\n']

    for item in json_results['items']:

        for channel in channels:
            if item in channel['items']:
                ch = channel['channel_label']
                content = item['alternatives'][0]['content']

                if item['type'] != 'punctuation':
                    if speaker != voices[ch]:
                        speaker = voices[ch]
                        start_time = str(datetime.timedelta(seconds=round(float(item['start_time']))))
                        text_lines.append(f'\n\n{speaker}:\n\n{start_time}\n')

                    if float(item['alternatives'][0]['confidence']) < 0.85:
                        content = f'**{content}**'

                elif text_lines[-1] == content:
                        continue

                text_lines.append(content)

    content = ' '.join(text_lines)
    content, count = re.subn(r' (?=[\.\,\?\!])', '', content)
    return Markup(markdown(content))

