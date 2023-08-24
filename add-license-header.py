from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from typing import NamedTuple

from identify import identify


class BlockComment(NamedTuple):
    start: str
    middle: str
    end: str


BLOCK_COMMENT = {
    'bash': BlockComment('', '# ', ''),
    'c#': BlockComment('/*', ' * ', ' */'),
    'c': BlockComment('/*', ' * ', ' */'),
    'c++': BlockComment('/*', ' * ', ' */'),
    'css': BlockComment('/*', ' * ', ' */'),
    'go': BlockComment('/*', ' * ', ' */'),
    'groovy': BlockComment('/*', ' * ', ' */'),
    'html': BlockComment('<!--', '', '-->'),
    'java': BlockComment('/*', ' * ', ' */'),
    'javascript': BlockComment('/*', ' * ', ' */'),
    'jsx': BlockComment('/*', ' * ', ' */'),
    'kotlin': BlockComment('/*', ' * ', ' */'),
    'lua': BlockComment('--[[', '', '--]]'),
    'makefile': BlockComment('', '# ', ''),
    'php': BlockComment('/*', ' * ', ' */'),
    'python': BlockComment('', '# ', ''),
    'ruby': BlockComment('', '# ', ''),
    'rust': BlockComment('/*', ' * ', ' */'),
    'scala': BlockComment('/*', ' * ', ' */'),
    'swift': BlockComment('/*', ' * ', ' */'),
    'terraform': BlockComment('/*', ' * ', ' */'),
    'toml': BlockComment('', '# ', ''),
    'ts': BlockComment('/*', ' * ', ' */'),
    'tsx': BlockComment('/*', ' * ', ' */'),
    'yaml': BlockComment('', '# ', ''),
    'zsh': BlockComment('', '# ', ''),
}

RE_AUTHOR_NAME = re.compile(r'\${author_name}')
RE_END_YEAR = re.compile(r'\${end_year}')
RE_START_YEAR = re.compile(r'\${start_year}')

WRAP_LICENSE_IN_COMMENTS_CACHE: dict[str, list[str]] = {}


def _wrap_license_in_comments(
    license_fmt: list[str],
    file_type: str,
) -> list[str]:
    if file_type in WRAP_LICENSE_IN_COMMENTS_CACHE:
        return WRAP_LICENSE_IN_COMMENTS_CACHE[file_type]

    header = list(license_fmt)

    if file_type in BLOCK_COMMENT:
        comment = BLOCK_COMMENT[file_type]

        if comment.middle:
            for i in range(len(license_fmt)):
                if header[i] == '\n':
                    header[i] = f'{comment.middle}'.rstrip(' ') + '\n'
                else:
                    header[i] = f'{comment.middle}{header[i]}'

        if comment.start:
            header.insert(0, f'{comment.start}\n')

        if comment.end:
            header.append(f'{comment.end}\n')

    WRAP_LICENSE_IN_COMMENTS_CACHE[file_type] = header
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


def _has_license_header(
    contents: list[str],
    license_header: list[str],
) -> bool:
    # Find where license should start
    i = 0
    while (
        i < len(contents) and
        (contents[i].startswith('#!') or contents[i] == '\n')
    ):
        i += 1

    # Check if matches expected license
    j = 0
    while (
        i < len(contents) and
        j < len(license_header) and
        contents[i] == license_header[j]
    ):
        i += 1
        j += 1

    return j >= len(license_header)


def _add_license_header(
    filename: str,
    license_formatted: list[str],
    *,
    dry_run: bool,
) -> int:
    file_types = identify.tags_from_path(filename)

    if 'binary' in file_types:
        print(
            f'cannot add license to binary file: {filename}',
            file=sys.stderr,
        )
        return 1

    for ft in file_types:
        if ft in BLOCK_COMMENT:
            file_type = ft
            break
    else:
        print(f'unsupported file format: {filename}', file=sys.stderr)
        print(
            'feel to open an issue/pr at '
            'https://github.com/arkinmodi/add-license-header to add support!',
            file=sys.stderr,
        )
        return 1

    license_header = _wrap_license_in_comments(license_formatted, file_type)

    with open(filename) as f:
        contents_text = f.readlines()

    if not _has_license_header(contents_text, license_header):
        print(f'adding license to {filename}', file=sys.stderr)
        if not dry_run:
            if len(contents_text) > 0 and contents_text[0].startswith('#!'):
                with open(filename, 'w') as f:
                    f.write(contents_text[0])

                    f.write('\n')
                    for text in license_header:
                        f.write(text)
                    f.write('\n')

                    for i in range(1, len(contents_text)):
                        f.write(contents_text[i])
            else:
                with open(filename, 'w') as f:
                    for text in license_header:
                        f.write(text)
                    f.write('\n')

                    for text in contents_text:
                        f.write(text)

        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
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
            dry_run=args.dry_run,
        )
    return return_code


if __name__ == '__main__':
    raise SystemExit(main())
