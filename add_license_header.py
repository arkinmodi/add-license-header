from __future__ import annotations

import argparse
import re
import sys
from datetime import date
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

RE_AUTHOR_NAME = re.compile(r'\${author_name}')
RE_END_YEAR = re.compile(r'\${end_year}')
RE_START_YEAR = re.compile(r'\${start_year}')

ALH_HEADER = 'LICENSE HEADER MANAGED BY add-license-header'

WRAP_LICENSE_IN_COMMENTS_CACHE: dict[BlockComment, list[str]] = {}


def _wrap_license_in_comments(
    license_fmt: list[str],
    file_type: str,
) -> list[str]:
    comment = BLOCK_COMMENT[file_type]

    if comment in WRAP_LICENSE_IN_COMMENTS_CACHE:
        return WRAP_LICENSE_IN_COMMENTS_CACHE[comment]

    header = license_fmt[:]

    for i in range(len(header)):
        if header[i] == '\n':
            header[i] = f'{comment.middle}\n'
        else:
            header[i] = f'{comment.middle} {header[i]}'

    header.insert(0, f'{comment.middle}\n')
    header.insert(0, f'{comment.start} {ALH_HEADER}\n')

    if comment.end != comment.middle:
        header.append(f'{comment.end}\n')

    WRAP_LICENSE_IN_COMMENTS_CACHE[comment] = header
    return header


def _build_license_header(
    filename: str,
    *,
    start_year: str,
    end_year: str,
    author_name: str,
) -> list[str]:
    with open(filename) as f:
        license_template = f.readlines()

    for i, line in enumerate(license_template):
        line = RE_START_YEAR.sub(start_year, line)
        line = RE_END_YEAR.sub(end_year, line)
        line = RE_AUTHOR_NAME.sub(author_name, line)
        license_template[i] = line.rstrip() + '\n'

    return license_template


def _update_license_header(
    *,
    contents: list[str],
    file_type: str,
    license_header: list[str],
) -> list[str]:
    comment = BLOCK_COMMENT[file_type]
    # Find start of license header
    i = 0
    while i < len(contents) and contents[i] != license_header[0]:
        i += 1

    if i == len(contents):  # License header not in file, so add it
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
        # Check where license header ends
        j = i
        while (
            j < len(contents) and
            (
                contents[j].startswith(comment.start) or
                contents[j].startswith(comment.middle) or
                contents[j].startswith(comment.end)
            )
        ):
            j += 1
        new_contents = contents[:i] + license_header + contents[j:]
    return new_contents


class UnknownFileTypeException(Exception):
    pass


class BinaryFileTypeException(Exception):
    pass


def _get_file_type(filename: str) -> str:
    identify_tags = identify.tags_from_path(filename)

    if 'binary' in identify_tags:
        raise BinaryFileTypeException(
            f'cannot add license to binary file: {filename}',
        )

    for tag in identify_tags:
        if tag in BLOCK_COMMENT:
            file_type = tag
            break
    else:
        raise UnknownFileTypeException(f'unsupported file format: {filename}')
    return file_type


def _add_license_header(
    filename: str,
    license_formatted: list[str],
    *,
    dry_run: bool,
) -> int:
    try:
        file_type = _get_file_type(filename)
    except UnknownFileTypeException:
        print(f'unsupported file format: {filename}', file=sys.stderr)
        print(
            'feel to open an issue/pr at '
            'https://github.com/arkinmodi/add-license-header to add support!',
            file=sys.stderr,
        )
        return -1
    except BinaryFileTypeException:
        print(
            f'cannot add license to a binary file: {filename}',
            file=sys.stderr,
        )
        return -1

    license_header = _wrap_license_in_comments(license_formatted, file_type)

    with open(filename) as f:
        contents_text = f.readlines()

    new_contents = _update_license_header(
        contents=contents_text,
        file_type=file_type,
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
    parser.add_argument('--check', action='store_true')
    parser.add_argument(
        '--license',
        required=True,
        help='path to license template',
    )
    parser.add_argument('--start-year', default=str(date.today().year))
    parser.add_argument('--end-year', default=str(date.today().year))
    parser.add_argument('--author-name', default='')
    parser.add_argument('filenames', nargs='*')
    args = parser.parse_args()

    license_formatted = _build_license_header(
        args.license,
        start_year=args.start_year,
        end_year=args.end_year,
        author_name=args.author_name,
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
