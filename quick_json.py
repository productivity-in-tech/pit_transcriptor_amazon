from pathlib import Path
import json
import click

@click.group()
def cli():
    pass

@cli.command()
@click.argument('path')
def parse(path):
    json_parse(path)


def json_parse(path):
    with open(path) as f:
        jsonfile = json.load(f)
        transcript = jsonfile['results']['transcripts'][0]['transcript']
        Path(path).with_suffix('.txt').write_text('\n'.join(transcript.split('.')))


@cli.command()
@click.argument('directory')
def bulk(directory):
    for path in Path(directory).rglob('*.json'):
        json_parse(path)

if __name__ == '__main__':
    cli()
