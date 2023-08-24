from __future__ import annotations

import argparse
import sys
from typing import NamedTuple

from identify import identify


class BlockComment(NamedTuple):
    start: str
    middle: str
    end: str


BLOCK_COMMENT = {
    'java': BlockComment('/*', ' * ', ' */'),
    'javascript': BlockComment('/*', ' * ', ' */'),
    'python': BlockComment('', '# ', ''),
    'ts': BlockComment('/*', ' * ', ' */'),
}


def _wrap_license_in_comments(
    license_fmt: list[str],
    file_type: str,
) -> list[str]:
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

    return header


def _build_license_header(license_filename: str) -> list[str]:
    with open(license_filename) as f:
        license_template = f.readlines()

    # TODO: license template stuff
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


def _add_license_header(filename: str, license_formatted: list[str]) -> int:
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
        return 1

    license_header = _wrap_license_in_comments(license_formatted, file_type)

    with open(filename) as f:
        contents_text = f.readlines()

    if not _has_license_header(contents_text, license_header):
        print(f'adding license to {filename}', file=sys.stderr)

        if len(contents_text) > 0 and contents_text[0].startswith('#!'):
            with open(filename, 'w') as f:
                f.write(contents_text[0])

                f.write('\n')
                for text in license_header:
                    f.write(text)

                for i in range(1, len(contents_text)):
                    f.write(contents_text[i])
        else:
            with open(filename, 'w') as f:
                for text in license_header:
                    f.write(text)

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
    # parser.add_argument('--start-year')
    # parser.add_argument('--end-year')
    parser.add_argument('filenames', nargs='*')
    args = parser.parse_args()

    license_formatted = _build_license_header(args.license)
    return_code = 0
    for filename in args.filenames:
        return_code |= _add_license_header(filename, license_formatted)
    return return_code


if __name__ == '__main__':
    raise SystemExit(main())
