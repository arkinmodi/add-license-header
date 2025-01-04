from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from add_license_header import BinaryFileTypeException
from add_license_header import BLOCK_COMMENT
from add_license_header import BlockComment
from add_license_header import get_block_comment
from add_license_header import main
from add_license_header import UnknownFileTypeException
from add_license_header import wrap_license_in_comments


def test_get_block_comment_regular_file(tmp_path):
    f = tmp_path.joinpath('t.py')
    f.write_text('print("Hello World")')
    assert get_block_comment(f) == BLOCK_COMMENT['python']


def test_get_block_comment_binary_file(tmp_path):
    f = tmp_path.joinpath('t.exe')
    f.write_text('binary file')
    with pytest.raises(BinaryFileTypeException):
        get_block_comment(f)


def test_get_block_comment_unsupported_file(tmp_path):
    f = tmp_path.joinpath('unsupported')
    f.write_text('unsupported')
    with pytest.raises(UnknownFileTypeException):
        get_block_comment(f)


@pytest.mark.parametrize(
    ('license_fmt', 'block_comment', 'is_managed', 'expected'),
    (
        pytest.param(
            'TEST LICENSE\n\nthis is a test license\n',
            BlockComment('#', '#', '#'),
            True,
            [
                '# LICENSE HEADER MANAGED BY add-license-header\n',
                '#\n',
                '# TEST LICENSE\n',
                '#\n',
                '# this is a test license\n',
                '#\n',
            ],
            id='all symbols same in block comment',
        ),
        pytest.param(
            'TEST LICENSE\nthis is a test license\n',
            BlockComment('/*', ' *', '*/'),
            True,
            [
                '/* LICENSE HEADER MANAGED BY add-license-header\n',
                ' *\n',
                ' * TEST LICENSE\n',
                ' * this is a test license\n',
                '*/\n',
            ],
            id='all different symbols in block comment',
        ),
        pytest.param(
            'TEST LICENSE\nthis is a test license\n',
            BlockComment('<!--', '', '-->'),
            True,
            [
                '<!-- LICENSE HEADER MANAGED BY add-license-header\n',
                '\n',
                'TEST LICENSE\n',
                'this is a test license\n',
                '-->\n',
            ],
            id='middle symbol is blank in block comment',
        ),
    ),
)
def test_wrap_license_in_comments(
        license_fmt,
        block_comment,
        is_managed,
        expected,
):
    wrap_license_in_comments.cache_clear()
    assert wrap_license_in_comments(
        license_fmt,
        block_comment,
        is_managed,
    ) == expected


@pytest.mark.parametrize(
    ('contents', 'license_template', 'expected'),
    (
        pytest.param(
            'print("Hello World")\n',
            (
                'TEST LICENSE\n'
                'this is a test license\n'
                '$create_year\n'
                '$edit_year\n'
                '$author_name\n'
            ),
            (
                '# LICENSE HEADER MANAGED BY add-license-header\n'
                '#\n'
                '# TEST LICENSE\n'
                '# this is a test license\n'
                '# 2023\n'
                '# 2024\n'
                '# John Smith\n'
                '#\n'
                '\n'
                'print("Hello World")\n'
            ),
            id='regular file without header',
        ),
        pytest.param(
            (
                '#!/usr/bin/env python3\n'
                'print("Hello World")\n'
            ),
            (
                'TEST LICENSE\n'
                'this is a test license\n'
            ),
            (
                '#!/usr/bin/env python3\n'
                '\n'
                '# LICENSE HEADER MANAGED BY add-license-header\n'
                '#\n'
                '# TEST LICENSE\n'
                '# this is a test license\n'
                '#\n'
                '\n'
                'print("Hello World")\n'
            ),
            id='executable file without header',
        ),
        pytest.param(
            (
                '# LICENSE HEADER MANAGED BY add-license-header\n'
                '#\n'
                '# OLD TEST LICENSE\n'
                '#\n'
                '\n'
                'print("Hello World")\n'
            ),
            (
                'NEW TEST LICENSE\n'
                'this is a test license\n'
            ),
            (
                '# LICENSE HEADER MANAGED BY add-license-header\n'
                '#\n'
                '# NEW TEST LICENSE\n'
                '# this is a test license\n'
                '#\n'
                '\n'
                'print("Hello World")\n'
            ),
            id='regular file with old header that is shorter than new header',
        ),
        pytest.param(
            (
                '# LICENSE HEADER MANAGED BY add-license-header\n'
                '#\n'
                '# OLD TEST LICENSE\n'
                '# this is a test license\n'
                '#\n'
                '\n'
                'print("Hello World")\n'
            ),
            (
                'NEW TEST LICENSE\n'
            ),
            (
                '# LICENSE HEADER MANAGED BY add-license-header\n'
                '#\n'
                '# NEW TEST LICENSE\n'
                '#\n'
                '\n'
                'print("Hello World")\n'
            ),
            id='regular file with old header that is longer than new header',
        ),
    ),
)
def test_main(contents, license_template, expected, tmp_path):
    f = tmp_path.joinpath('t.py')
    f.write_text(contents)

    return_code = main([
        '--author-name', 'John Smith',
        '--create-year', '2023',
        '--edit-year', '2024',
        '--license', license_template,
        f.resolve().as_posix(),
    ])

    assert return_code == 1
    assert f.read_text() == expected

    # Run again to ensure we have reached a steady state
    return_code = main([
        '--author-name', 'John Smith',
        '--create-year', '2023',
        '--edit-year', '2024',
        '--license', license_template,
        f.resolve().as_posix(),
    ])

    assert return_code == 0
    assert f.read_text() == expected


@pytest.mark.parametrize(
    ('filename', 'contents', 'license_template', 'expected'),
    (
        pytest.param(
            't.py',
            'print("Hello World")\n',
            (
                'TEST LICENSE\n'
                'this is a test license\n'
                '$create_year\n'
                '$edit_year\n'
                '$author_name\n'
            ),
            (
                '#\n'
                '# TEST LICENSE\n'
                '# this is a test license\n'
                '# 2023\n'
                '# 2024\n'
                '# John Smith\n'
                '#\n'
                '\n'
                'print("Hello World")\n'
            ),
            id='add license header to file',
        ),
        pytest.param(
            't.py',
            '# first line\nprint("Hello World")\n',
            (
                'TEST LICENSE\n'
                'this is a test license\n'
                '$create_year\n'
                '$edit_year\n'
                '$author_name\n'
            ),
            (
                '# first line\n'
                '# TEST LICENSE\n'
                '# this is a test license\n'
                '# 2023\n'
                '# 2024\n'
                '# John Smith\n'
                '#\n'
                'print("Hello World")\n'
            ),
            id='existing single line comment',
        ),
        pytest.param(
            't.md',
            '<!--first line-->\n# Hello\n',
            (
                'TEST LICENSE\n'
                'this is a test license\n'
                '$create_year\n'
                '$edit_year\n'
                '$author_name\n'
            ),
            (
                '<!--\n'
                'TEST LICENSE\n'
                'this is a test license\n'
                '2023\n'
                '2024\n'
                'John Smith\n'
                '-->\n'
                '\n'
                '<!--first line-->\n'
                '# Hello\n'
            ),
            id='add license header to file with single line comment block',
        ),
    ),
)
def test_main_unmanaged(
    filename,
    contents,
    license_template,
    expected,
    tmp_path,
):
    f = tmp_path.joinpath(filename)
    f.write_text(contents)

    return_code = main([
        '--author-name', 'John Smith',
        '--create-year', '2023',
        '--edit-year', '2024',
        '--license', license_template,
        '--unmanaged',
        f.resolve().as_posix(),
    ])

    assert return_code == 1
    assert f.read_text() == expected

    # Run again to ensure we have reached a steady state
    return_code = main([
        '--author-name', 'John Smith',
        '--create-year', '2023',
        '--edit-year', '2024',
        '--license', license_template,
        '--unmanaged',
        f.resolve().as_posix(),
    ])

    assert return_code == 0
    assert f.read_text() == expected


def test_main_file_type_with_diffent_comment_block_characters(tmp_path):
    license_template = (
        'TEST LICENSE\n'
        'this is a test license\n'
    )
    f = tmp_path.joinpath('main.java')
    f.write_text('''\
/* LICENSE HEADER MANAGED BY add-license-header
 *
 * OLD TEST LICENSE
 */

public class Main {
    public static void main(String args[]) {
        System.out.println("hello, world");
    }
}
''')

    return_code = main([
        '--create-year', '2023',
        '--license', license_template,
        f.resolve().as_posix(),
    ])

    expected = """\
/* LICENSE HEADER MANAGED BY add-license-header
 *
 * TEST LICENSE
 * this is a test license
 */

public class Main {
    public static void main(String args[]) {
        System.out.println("hello, world");
    }
}
"""
    assert return_code == 1
    assert f.read_text() == expected


@pytest.mark.parametrize(
    ('contents', 'license_template'),
    (
        pytest.param(
            (
                '# LICENSE HEADER MANAGED BY add-license-header\n'
                '#\n'
                '# TEST LICENSE\n'
                '# this is a test license\n'
                '#\n'
                '\n'
                'print("Hello World")\n'
            ),
            (
                'TEST LICENSE\n'
                'this is a test license\n'
            ),
            id='regular file',
        ),
        pytest.param(
            (
                '#!/usr/bin/env python3\n'
                '\n'
                '# LICENSE HEADER MANAGED BY add-license-header\n'
                '#\n'
                '# TEST LICENSE\n'
                '# this is a test license\n'
                '#\n'
                '\n'
                'print("Hello World")\n'
            ),
            (
                'TEST LICENSE\n'
                'this is a test license\n'
            ),
            id='executable file',
        ),
    ),
)
def test_main_no_change(contents, license_template, tmp_path):
    f = tmp_path.joinpath('t.py')
    f.write_text(contents)

    return_code = main([
        '--create-year', '2023',
        '--license', license_template,
        f.resolve().as_posix(),
    ])

    assert return_code == 0
    assert f.read_text() == contents


@pytest.mark.parametrize(
    ('filename', 'contents'),
    (
        pytest.param(
            't.unsupported',
            'unsupported',
            id='unsupported file type',
        ),
        pytest.param(
            'unsupported',
            '#!/usr/bin/env unsupported\n',
            id='unsupported executable file',
        ),
        pytest.param(
            't.exe',
            'binary file',
            id='binary file',
        ),
    ),
)
def test_main_unsupported_file(filename, contents, tmp_path):
    license_file = tmp_path.joinpath('license')
    license_file.write_text(
        'TEST LICENSE\n'
        'this is a test license\n'
        '$create_year\n'
        '$edit_year\n'
        '$author_name\n',
    )
    f = tmp_path.joinpath(filename)
    f.write_text(contents)

    return_code = main([
        '--license-file', license_file.resolve().as_posix(),
        '--create-year', '2023',
        '--edit-year', '2024',
        '--author-name', 'John Smith',
        '--check',
        f.resolve().as_posix(),
    ])

    assert return_code == 1


@patch('add_license_header.subprocess.run')
def test_main_use_defaults_and_git_failed(mock_run, tmp_path):
    license_file = tmp_path.joinpath('license')
    license_file.write_text(
        'TEST LICENSE\n'
        'this is a test license\n'
        '$create_year$year_delimiter$edit_year\n'
        '$author_name\n',
    )
    f = tmp_path.joinpath('t.py')
    f.write_text('print("Hello World")\n')

    mock_git_stdout = MagicMock()
    mock_git_stdout.configure_mock(
        **{
            'returncode': 1,
        },
    )
    mock_run.return_value = mock_git_stdout

    return_code = main([
        '--license-file', license_file.resolve().as_posix(),
        f.resolve().as_posix(),
    ])

    expected = f"""\
# LICENSE HEADER MANAGED BY add-license-header
#
# TEST LICENSE
# this is a test license
# {date.today().year}, {date.today().year}
#

print("Hello World")
"""
    assert f.read_text() == expected
    assert return_code == 1


def test_main_check_mode(tmp_path):
    f = tmp_path.joinpath('t.py')
    f.write_text('print("Hello World")\n')

    license_template = (
        'TEST LICENSE\n'
        'this is a test license\n'
    )
    return_code = main([
        '--create-year', '2023',
        '--license', license_template,
        '--check',
        f.resolve().as_posix(),
    ])

    assert return_code == 1
    assert f.read_text() == 'print("Hello World")\n'


def test_main_exit_zero(tmp_path):
    f = tmp_path.joinpath('t.py')
    f.write_text('print("Hello World")\n')

    license_template = (
        'TEST LICENSE\n'
        'this is a test license\n'
    )
    return_code = main([
        '--create-year', '2023',
        '--license', license_template,
        '--exit-zero',
        f.resolve().as_posix(),
    ])

    expected = """\
# LICENSE HEADER MANAGED BY add-license-header
#
# TEST LICENSE
# this is a test license
#

print("Hello World")
"""
    assert return_code == 0
    assert f.read_text() == expected


def test_main_exit_zero_if_unsupported_file_type(tmp_path):
    f = tmp_path.joinpath('unsupported')
    f.write_text('unsupported')

    license_template = (
        'TEST LICENSE\n'
        'this is a test license\n'
    )

    return_code = main([
        '--create-year', '2023',
        '--license', license_template,
        '--exit-zero-if-unsupported',
        f.resolve().as_posix(),
    ])

    assert return_code == 0


@patch('add_license_header.subprocess.run')
def test_main_create_year_from_git(mock_run, tmp_path):
    f = tmp_path.joinpath('t.py')
    f.write_text('print("Hello World")\n')

    license_template = (
        'TEST LICENSE\n'
        'this is a test license\n'
        '$create_year\n'
    )

    mock_git_stdout = MagicMock()
    mock_git_stdout.configure_mock(
        **{
            'stdout': '2023\n1999\n',
            'returncode': 0,
        },
    )
    mock_run.return_value = mock_git_stdout

    return_code = main([
        '--license', license_template,
        f.resolve().as_posix(),
    ])

    expected = """\
# LICENSE HEADER MANAGED BY add-license-header
#
# TEST LICENSE
# this is a test license
# 1999
#

print("Hello World")
"""
    assert return_code == 1
    assert f.read_text() == expected


@patch('add_license_header.subprocess.run')
def test_main_single_year_if_same(mock_run, tmp_path):
    f = tmp_path.joinpath('t.py')
    f.write_text('print("Hello World")\n')

    mock_git_stdout = MagicMock()
    mock_git_stdout.configure_mock(
        **{
            'returncode': 1,
        },
    )
    mock_run.return_value = mock_git_stdout

    license_template = (
        'TEST LICENSE\n'
        'this is a test license\n'
        '$create_year$year_delimiter$edit_year\n'
    )

    return_code = main([
        '--license', license_template,
        '--single-year-if-same',
        f.resolve().as_posix(),
    ])

    expected = f"""\
# LICENSE HEADER MANAGED BY add-license-header
#
# TEST LICENSE
# this is a test license
# {date.today().year}
#

print("Hello World")
"""
    assert return_code == 1
    assert f.read_text() == expected
