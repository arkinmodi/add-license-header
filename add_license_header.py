from __future__ import annotations

import argparse
import functools
import string
import subprocess
import sys
from datetime import date
from typing import NamedTuple
from typing import Sequence
from typing import TypedDict

from identify import identify


class BlockComment(NamedTuple):
    start: str
    middle: str
    end: str


# NOTE: Must be minimal characters to create a comment. Leading and trailing
# spaces are allowed.
BLOCK_COMMENT = {
    'bash': BlockComment('#', '#', '#'),
    'c#': BlockComment('/*', ' *', ' */'),
    'c': BlockComment('/*', ' *', ' */'),
    'c++': BlockComment('/*', ' *', ' */'),
    'css': BlockComment('/*', ' *', ' */'),
    'gherkin': BlockComment('#', '#', '#'),
    'go': BlockComment('/*', ' *', ' */'),
    'groovy': BlockComment('/*', ' *', ' */'),
    'html': BlockComment('<!--', '', '-->'),
    'java': BlockComment('/*', ' *', ' */'),
    'javascript': BlockComment('/*', ' *', ' */'),
    'jsx': BlockComment('/*', ' *', ' */'),
    'kotlin': BlockComment('/*', ' *', ' */'),
    'lua': BlockComment('--[[', '', '--]]'),
    'makefile': BlockComment('#', '#', '#'),
    'markdown': BlockComment('<!--', '', '-->'),
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
        formatted_license: str,
        comment: BlockComment,
        is_managed: bool,
) -> list[str]:
    header = formatted_license.splitlines()
    if header[-1] == '':
        header.pop()

    for i in range(len(header)):
        if header[i] == '':
            header[i] = f'{comment.middle}\n'
        elif comment.middle != '':
            header[i] = f'{comment.middle} {header[i]}\n'
        else:
            header[i] += '\n'

    if is_managed:
        header.insert(0, f'{comment.middle}\n')
        header.insert(0, f'{comment.start} {ALH_HEADER}\n')
    else:
        header.insert(0, f'{comment.start}\n')

    header.append(f'{comment.end}\n')
    return header


def get_create_year(filepath: str) -> int:
    create_year = subprocess.run(
        (
            'git',
            'log',
            '--format=%ad',
            '--date=format:%Y',
            filepath,
        ),
        capture_output=True,
        encoding='UTF-8',
    )
    if create_year.returncode != 0 or not create_year.stdout:
        # assuming this is a new file
        return date.today().year
    return int(create_year.stdout.splitlines()[-1])


class FormatLicenseFields(TypedDict):
    author_name: str
    create_year: int | None
    edit_year: int
    year_delimiter: str


def format_license(
        filepath: str,
        license_template: str,
        single_year_if_same: bool,
        license_fields: FormatLicenseFields,
) -> str:
    author_name = license_fields['author_name']
    create_year = license_fields['create_year']
    edit_year = license_fields['edit_year']
    year_delimiter = license_fields['year_delimiter']

    if create_year is None:
        create_year = get_create_year(filepath)

    if single_year_if_same and create_year == edit_year:
        return string.Template(license_template).safe_substitute({
            'author_name': author_name,
            'create_year': create_year,
            'edit_year': '',
            'year_delimiter': '',
        })
    return string.Template(license_template).safe_substitute({
        'author_name': author_name,
        'create_year': create_year,
        'edit_year': edit_year,
        'year_delimiter': year_delimiter,
    })


def update_license_header(
        contents: list[str],
        comment: BlockComment,
        wrapped_license: list[str],
) -> list[str]:
    if len(contents) > 0 and contents[0].startswith('#!'):
        header_start_index = 1
    else:
        header_start_index = 0
    comment_start = wrapped_license[0].strip()

    while (
        header_start_index < len(contents) and
        not contents[header_start_index].startswith(comment_start)
    ):
        header_start_index += 1

    if header_start_index == len(contents):
        # License header not in file, so add it
        if len(contents) > 0 and contents[0].startswith('#!'):
            new_contents = [
                contents[0],
                '\n',
                *wrapped_license,
                '\n',
                *contents[1:],
            ]
        else:
            new_contents = [*wrapped_license, '\n'] + contents
    else:
        # License header is in file, so update it
        header_end_index = header_start_index + 1
        if comment.middle == comment.end:
            while (
                header_end_index < len(contents) and
                contents[header_end_index].startswith(comment.end)
            ):
                header_end_index += 1
        else:
            commend_end = comment.end.strip()
            while (
                header_end_index < len(contents) and
                not contents[header_end_index].rstrip().endswith(commend_end)
            ):
                header_end_index += 1
            header_end_index += 1

        # NOTE: The list slicing done here is to preserve the original comment
        # block beginning and ending lines. For example, Java's comment blocks
        # start with '/*', however, '/**' is a popular starting line. This is
        # to preserve this style choice.
        new_contents = (
            contents[:header_start_index + 1] +
            wrapped_license[1:-1] +
            contents[header_end_index - 1:]
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
    raise UnknownFileTypeException(f'unsupported file format: {filename}')


def add_license_header(
        filepath: str,
        license_template: str,
        license_fields: FormatLicenseFields,
        is_managed: bool,
        single_year_if_same: bool,
        exit_zero_if_unsupported: bool,
        *,
        dry_run: bool,
) -> int:
    try:
        block_comment = get_block_comment(filepath)
    except UnknownFileTypeException:
        print(f'unsupported file format: {filepath}', file=sys.stderr)
        return 0 if exit_zero_if_unsupported else 1
    except BinaryFileTypeException:
        print(
            f'cannot add license to a binary file: {filepath}',
            file=sys.stderr,
        )
        return 0 if exit_zero_if_unsupported else 1

    formatted_license = format_license(
        filepath,
        license_template,
        single_year_if_same,
        license_fields,
    )
    license_header = wrap_license_in_comments(
        formatted_license,
        block_comment,
        is_managed,
    )

    with open(filepath) as f:
        contents_text = f.readlines()

    new_contents = update_license_header(
        contents_text,
        block_comment,
        license_header,
    )

    if new_contents != contents_text:
        print(f'updating license in {filepath}', file=sys.stderr)
        if not dry_run:
            with open(filepath, 'w') as f:
                f.write(''.join(new_contents))
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            'A tool for automatically adding your license as a header in your '
            'source code.'
        ),
    )
    parser.add_argument(
        '--author-name',
        default='',
        help='Value to replace $author_name. Defaults to empty string.',
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help=(
            'Only checks if files are update to date. Will not apply any '
            'changes.'
        ),
    )
    parser.add_argument(
        '--create-year',
        help=(
            'Value to replace $create_year. Defaults to looking up creation '
            'date in git history. If that fails, will be defaulted to the '
            'current year.'
        ),
    )
    parser.add_argument(
        '--exit-zero',
        action='store_true',
        help='Always exit with a return code of 0.',
    )
    parser.add_argument(
        '--exit-zero-if-unsupported',
        action='store_true',
        help='Exit with a return code of 0 if file type is unsupported.',
    )
    parser.add_argument(
        '--edit-year',
        default=date.today().year,
        help='Value to replace $edit_year. Defaults to current year.',
    )
    parser.add_argument(
        '--single-year-if-same',
        action='store_true',
        help=(
            'If the $create_year and $edit_year are the same, only the '
            '$create_year will be inserted. The $edit_year and '
            '$year_delimiter will be replaced with the empty string.'
        ),
    )
    parser.add_argument(
        '--unmanaged',
        action='store_true',
        help=(
            'When running in unmanaged mode, the "LICENSE HEADER MANAGED BY '
            'add-license-header" will not be added to the license header. '
            'Instead the first comment in the file will be considered to be '
            'the license header (with the exception of shebangs). Running in '
            'managed mode enables you to have the license located anywhere in '
            'the file.'
        ),
    )
    parser.add_argument(
        '--year-delimiter',
        default=', ',
        help='Value to replace $year_delimiter. Defaults to ", ".',
    )

    license_group = parser.add_mutually_exclusive_group(required=True)
    license_group.add_argument(
        '--license-file',
        help='Path to license template file.',
    )
    license_group.add_argument('--license', help='License template.')

    parser.add_argument('filenames', help='File paths to check.', nargs='*')
    args = parser.parse_args(argv)

    if args.license_file is not None:
        with open(args.license_file) as f:
            license_template = f.read()
    else:
        license_template = bytes(
            args.license,
            'utf-8',
        ).decode('unicode_escape')

    return_code = 0
    for filename in args.filenames:
        return_code |= add_license_header(
            filename,
            license_template,
            {
                'author_name': args.author_name,
                'create_year': args.create_year,
                'edit_year': args.edit_year,
                'year_delimiter': args.year_delimiter,
            },
            not args.unmanaged,
            args.single_year_if_same,
            args.exit_zero_if_unsupported,
            dry_run=args.check,
        )
    return return_code if not args.exit_zero else 0


if __name__ == '__main__':
    raise SystemExit(main())
