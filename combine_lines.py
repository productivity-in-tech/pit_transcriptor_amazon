import re
import click
from pathlib import Path

@click.command()
@click.option('--marker-file')
@click.option('--content-file')
def parse(marker_file: str, content_file: str):
    lines = Path(marker_file).read_text()
    marker_items = re.findall(r'\d{2}:\d{2}(?=\.)', lines)

    with open(content_file) as content:
        content_items = content.readlines()

    final_file = Path(content_file).parent.joinpath(
            Path(f'{Path(content_file).stem}-final.txt')
    )

    if (marker_count:=len(marker_items)) != (content_count:=len(content_items)):
        raise ValueError(f'Line Mismatch. Check your \
Markers and try again\n{marker_count=}\n{content_count=}')

    final_lines = zip(marker_items, map(lambda x:x.lstrip(' '), content_items))


    with open(final_file, 'w') as final:
        final.writelines([f'{x} {y}' for x, y in final_lines])

if __name__ == '__main__':
    parse()
