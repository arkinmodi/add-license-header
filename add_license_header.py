from __future__ import annotations

import argparse
import functools
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import NamedTuple
from typing import Sequence

from identify import identify


class BlockComment(NamedTuple):
    start: str
    middle: str
    end: str


BLOCK_COMMENT = {
    'bash': BlockComment('#', '#', '#'),
    'c#': BlockComment('/*', ' *', ' */'),
    'c': BlockComment('/*', ' *', ' */'),
    'c++': BlockComment('/*', ' *', ' */'),
    'css': BlockComment('/*', ' *', ' */'),
    'go': BlockComment('/*', ' *', ' */'),
    'groovy': BlockComment('/*', ' *', ' */'),
    'html': BlockComment('<!--', '', '-->'),
    'java': BlockComment('/*', ' *', ' */'),
    'javascript': BlockComment('/*', ' *', ' */'),
    'jsx': BlockComment('/*', ' *', ' */'),
    'kotlin': BlockComment('/*', ' *', ' */'),
    'lua': BlockComment('--[[', '', '--]]'),
    'makefile': BlockComment('#', '#', '#'),
    'php': BlockComment('/*', ' *', ' */'),
    'python': BlockComment('#', '#', '#'),
    'ruby': BlockComment('#', '#', '#'),
    'rust': BlockComment('/*', ' *', ' */'),
    'scala': BlockComment('/*', ' *', ' */'),
    'swift': BlockComment('/*', ' *', ' */'),
    'terraform': BlockComment('/*', ' *', ' */'),
    'toml': BlockComment('#', '#', '#'),
    'ts': BlockComment('/*', ' *', ' */'),
    'tsx': BlockComment('/*', ' *', ' */'),
    'yaml': BlockComment('#', '#', '#'),
    'zsh': BlockComment('#', '#', '#'),
}

ALH_HEADER = 'LICENSE HEADER MANAGED BY add-license-header'


@functools.lru_cache
def wrap_license_in_comments(
    license_fmt: tuple[str, ...],
    comment: BlockComment,
) -> list[str]:
    header = list(license_fmt)

    for i in range(len(header)):
        if header[i] == '\n':
            header[i] = f'{comment.middle}\n'
        elif comment.middle != '':
            header[i] = f'{comment.middle} {header[i]}'

    header.insert(0, f'{comment.middle}\n')
    header.insert(0, f'{comment.start} {ALH_HEADER}\n')

    if comment.end != comment.middle:
        header.append(f'{comment.end}\n')
    return header


def build_license_header(
    license_template: list[str],
    *,
    start_year: str,
    end_year: str,
    author_name: str,
) -> tuple[str, ...]:
    re_author_name = re.compile(r'\${author_name}')
    re_end_year = re.compile(r'\${end_year}')
    re_start_year = re.compile(r'\${start_year}')

    for i, line in enumerate(license_template):
        line = re_start_year.sub(start_year, line)
        line = re_end_year.sub(end_year, line)
        line = re_author_name.sub(author_name, line)
        license_template[i] = line

    return tuple(license_template)


def update_license_header(
    *,
    contents: list[str],
    comment: BlockComment,
    license_header: list[str],
) -> list[str]:
    header_start_index = 0
    while (
        header_start_index < len(contents) and
        contents[header_start_index] != license_header[0]
    ):
        header_start_index += 1

    # License header not in file, so add it
    if header_start_index == len(contents):
        if len(contents) > 0 and contents[0].startswith('#!'):
            new_contents = [
                contents[0],
                '\n',
                *license_header,
                '\n',
                *contents[1:],
            ]
        else:
            new_contents = [*license_header, '\n'] + contents
    else:  # License header is in file, so update it
        header_end_index = header_start_index + 1
        if comment.middle == comment.end:
            while (
                header_end_index < len(contents) and
                contents[header_end_index].startswith(comment.end)
            ):
                header_end_index += 1
        else:
            while (
                header_end_index < len(contents) and
                not contents[header_end_index].startswith(comment.end)
            ):
                header_end_index += 1
            header_end_index += 1

        new_contents = (
            contents[:header_start_index] +
            license_header +
            contents[header_end_index:]
        )
    return new_contents


class UnknownFileTypeException(Exception):
    pass


class BinaryFileTypeException(Exception):
    pass


def get_block_comment(filename: str) -> BlockComment:
    identify_tags = identify.tags_from_path(filename)

    if 'binary' in identify_tags:
        raise BinaryFileTypeException(
            f'cannot add license to binary file: {filename}',
        )

    for tag in identify_tags:
        if tag in BLOCK_COMMENT:
            return BLOCK_COMMENT[tag]
    else:
        raise UnknownFileTypeException(f'unsupported file format: {filename}')


def _add_license_header(
    filename: str,
    license_formatted: tuple[str, ...],
    *,
    dry_run: bool,
) -> int:
    try:
        block_comment = get_block_comment(filename)
    except UnknownFileTypeException:
        print(f'unsupported file format: {filename}', file=sys.stderr)
        print(
            'feel to open an issue/pr at '
            'https://github.com/arkinmodi/add-license-header to add support!',
            file=sys.stderr,
        )
        return 1
    except BinaryFileTypeException:
        print(
            f'cannot add license to a binary file: {filename}',
            file=sys.stderr,
        )
        return 1

    license_header = wrap_license_in_comments(license_formatted, block_comment)

    with open(filename) as f:
        contents_text = f.readlines()

    new_contents = update_license_header(
        contents=contents_text,
        comment=block_comment,
        license_header=license_header,
    )

    if new_contents != contents_text:
        print(f'updating license in {filename}', file=sys.stderr)
        if not dry_run:
            with open(filename, 'w') as f:
                f.write(''.join(new_contents))
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--author-name', help='defaults to empty string')
    parser.add_argument('--check', action='store_true')
    parser.add_argument(
        '--config-file',
        help=(
            'path to configuration file '
            '(default: ".add-license-header.json")'
        ),
        default='.add-license-header.json',
    )
    parser.add_argument('--end-year', help='defaults to current year')
    parser.add_argument('--license', help='path to license template file')
    parser.add_argument('--start-year', help='defaults to current year')
    parser.add_argument('filenames', nargs='*')
    args = parser.parse_args(argv)

    config_file = Path(args.config_file)
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
    else:
        config = {}

    if args.license is not None:
        license_filename = args.license
    elif 'license' in config:
        license_filename = config['license']
    else:
        parser.print_usage(file=sys.stderr)
        print(
            'Error: missing license template. Set the license template with '
            'either the --license flag or the "license" field in the '
            'configuration file',
            file=sys.stderr,
        )
        return 1

    if args.start_year is not None:
        start_year = args.start_year
    elif 'start_year' in config:
        start_year = str(config['start_year'])
    else:
        start_year = str(date.today().year)

    if args.end_year is not None:
        end_year = args.end_year
    elif 'end_year' in config:
        end_year = str(config['end_year'])
    else:
        end_year = str(date.today().year)

    if args.author_name is not None:
        author_name = args.author_name
    elif 'author_name' in config:
        author_name = config['author_name']
    else:
        author_name = ''

    with open(license_filename) as f:
        license_template = f.readlines()

    license_formatted = build_license_header(
        license_template,
        start_year=start_year,
        end_year=end_year,
        author_name=author_name,
    )

    return_code = 0
    for filename in args.filenames:
        return_code |= _add_license_header(
            filename,
            license_formatted,
            dry_run=args.check,
        )
    return return_code


if __name__ == '__main__':
    raise SystemExit(main())
