from __future__ import annotations

import pytest

from add_license_header import BinaryFileTypeException
from add_license_header import BLOCK_COMMENT
from add_license_header import BlockComment
from add_license_header import build_license_header
from add_license_header import get_block_comment
from add_license_header import main
from add_license_header import UnknownFileTypeException
from add_license_header import update_license_header
from add_license_header import wrap_license_in_comments


@pytest.mark.parametrize(
    ('template', 'start_year', 'end_year', 'author_name', 'expected'),
    (
        pytest.param(
            ['${start_year}'], '2023', '', '', ('2023',),
            id='set start year',
        ),
        pytest.param(
            ['${end_year}'], '', '2023', '', ('2023',),
            id='set end year',
        ),
        pytest.param(
            ['${author_name}'], '', '', 'John Smith', ('John Smith',),
            id='set author name',
        ),
        pytest.param(
            ['${start_year} ${end_year}'], '2023', '2024', '', ('2023 2024',),
            id='multiple different template markers in the same line',
        ),
        pytest.param(
            ['${start_year} ${start_year}'], '2023', '', '', ('2023 2023',),
            id='multiple same template markers in the same line',
        ),
        pytest.param(
            ['${start_year}\n', '${end_year}\n'], '2023', '2024', '',
            ('2023\n', '2024\n'),
            id='multiple template markers in multiple lines',
        ),
        pytest.param(
            ['nothing'], '2023', '2024', 'John Smith', ('nothing',),
            id='no template markers',
        ),
    ),
)
def test_build_license_header(
    template,
    start_year,
    end_year,
    author_name,
    expected,
):
    assert build_license_header(
        template,
        start_year=start_year,
        end_year=end_year,
        author_name=author_name,
    ) == expected


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
    ('license_fmt', 'block_comment', 'expected'),
    (
        pytest.param(
            ('TEST LICENSE\n', '\n', 'this is a test license\n'),
            BlockComment('#', '#', '#'),
            [
                '# LICENSE HEADER MANAGED BY add-license-header\n',
                '#\n',
                '# TEST LICENSE\n',
                '#\n',
                '# this is a test license\n',
            ],
            id='all symbols same in block comment',
        ),
        pytest.param(
            ('TEST LICENSE\n', 'this is a test license\n'),
            BlockComment('/*', ' *', '*/'),
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
            ('TEST LICENSE\n', 'this is a test license\n'),
            BlockComment('<!--', '', '-->'),
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
def test_wrap_license_in_comments(license_fmt, block_comment, expected):
    wrap_license_in_comments.cache_clear()
    assert wrap_license_in_comments(license_fmt, block_comment) == expected


@pytest.mark.parametrize(
    ('contents', 'comment', 'license_header', 'expected'),
    (
        pytest.param(
            ['print("Hello World")\n'],
            BlockComment('#', '#', '#'),
            [
                '# LICENSE HEADER MANAGED BY add-license-header\n',
                '#\n',
                '# TEST LICENSE\n',
                '# this is a test license\n',
            ],
            [
                '# LICENSE HEADER MANAGED BY add-license-header\n',
                '#\n',
                '# TEST LICENSE\n',
                '# this is a test license\n',
                '\n',
                'print("Hello World")\n',
            ],
            id='regular file without header',
        ),
        pytest.param(
            ['#!/usr/bin/env python3\n', 'print("Hello World")\n'],
            BlockComment('#', '#', '#'),
            [
                '# LICENSE HEADER MANAGED BY add-license-header\n',
                '#\n',
                '# TEST LICENSE\n',
                '# this is a test license\n',
            ],
            [
                '#!/usr/bin/env python3\n',
                '\n',
                '# LICENSE HEADER MANAGED BY add-license-header\n',
                '#\n',
                '# TEST LICENSE\n',
                '# this is a test license\n',
                '\n',
                'print("Hello World")\n',
            ],
            id='executable file without header',
        ),
        pytest.param(
            [
                '# LICENSE HEADER MANAGED BY add-license-header\n',
                '#\n',
                '# OUT OF DATE LICENSE\n',
                '# this is an out of date license\n',
                '\n',
                'print("Hello World")\n',
            ],
            BlockComment('#', '#', '#'),
            [
                '# LICENSE HEADER MANAGED BY add-license-header\n',
                '#\n',
                '# TEST LICENSE\n',
                '# this is a test license\n',
            ],
            [
                '# LICENSE HEADER MANAGED BY add-license-header\n',
                '#\n',
                '# TEST LICENSE\n',
                '# this is a test license\n',
                '\n',
                'print("Hello World")\n',
            ],
            id='regular file with header',
        ),
        pytest.param(
            [
                '#!/usr/bin/env python3\n',
                '\n',
                '# LICENSE HEADER MANAGED BY add-license-header\n',
                '#\n',
                '# OUT OF DATE LICENSE\n',
                '# this is an out of date license\n',
                '\n',
                'print("Hello World")\n',
            ],
            BlockComment('#', '#', '#'),
            [
                '# LICENSE HEADER MANAGED BY add-license-header\n',
                '#\n',
                '# TEST LICENSE\n',
                '# this is a test license\n',
            ],
            [
                '#!/usr/bin/env python3\n',
                '\n',
                '# LICENSE HEADER MANAGED BY add-license-header\n',
                '#\n',
                '# TEST LICENSE\n',
                '# this is a test license\n',
                '\n',
                'print("Hello World")\n',
            ],
            id='executable file with header',
        ),
        pytest.param(
            [
                '<!-- LICENSE HEADER MANAGED BY add-license-header\n',
                '\n',
                'OUT OF DATE LICENSE\n',
                'this is an out of date license\n',
                '-->\n',
                '\n',
                'print("Hello World")\n',
            ],
            BlockComment('<!--', '', '-->'),
            [
                '<!-- LICENSE HEADER MANAGED BY add-license-header\n',
                '\n',
                'TEST LICENSE\n',
                'this is a test license\n',
                '-->\n',
            ],
            [
                '<!-- LICENSE HEADER MANAGED BY add-license-header\n',
                '\n',
                'TEST LICENSE\n',
                'this is a test license\n',
                '-->\n',
                '\n',
                'print("Hello World")\n',
            ],
            id='regular file with header and middle comment is a blank symbol',
        ),
        pytest.param(
            [
                '# LICENSE HEADER MANAGED BY add-license-header\n',
                '#\n',
                '# OUT OF DATE LICENSE\n',
                '\n',
                'print("Hello World")\n',
            ],
            BlockComment('#', '#', '#'),
            [
                '# LICENSE HEADER MANAGED BY add-license-header\n',
                '#\n',
                '# TEST LICENSE\n',
                '# this is a test license\n',
            ],
            [
                '# LICENSE HEADER MANAGED BY add-license-header\n',
                '#\n',
                '# TEST LICENSE\n',
                '# this is a test license\n',
                '\n',
                'print("Hello World")\n',
            ],
            id='regular file with old header that is shorter than new header',
        ),
        pytest.param(
            [
                '# LICENSE HEADER MANAGED BY add-license-header\n',
                '#\n',
                '# OUT OF DATE LICENSE\n',
                '# this is an out of date license\n',
                '\n',
                'print("Hello World")\n',
            ],
            BlockComment('#', '#', '#'),
            [
                '# LICENSE HEADER MANAGED BY add-license-header\n',
                '#\n',
                '# TEST LICENSE\n',
            ],
            [
                '# LICENSE HEADER MANAGED BY add-license-header\n',
                '#\n',
                '# TEST LICENSE\n',
                '\n',
                'print("Hello World")\n',
            ],
            id='regular file with old header that is longer than new header',
        ),
    ),
)
def test_update_license_header(contents, comment, license_header, expected):
    assert update_license_header(
        contents=contents,
        comment=comment,
        license_header=license_header,
    ) == expected


def test_main_add_header_to_regular_file(tmp_path):
    license_file = tmp_path.joinpath('license')
    license_file.write_text(
        'TEST LICENSE\n'
        'this is a test license\n'
        '${start_year}\n'
        '${end_year}\n'
        '${author_name}\n',
    )
    f = tmp_path.joinpath('t.py')
    f.write_text('print("Hello World")\n')

    return_code = main([
        '--license', license_file.resolve().as_posix(),
        '--start-year', '2023',
        '--end-year', '2024',
        '--author-name', 'John Smith',
        f.resolve().as_posix(),
    ])

    expected = """\
# LICENSE HEADER MANAGED BY add-license-header
#
# TEST LICENSE
# this is a test license
# 2023
# 2024
# John Smith

print("Hello World")
"""
    assert f.read_text() == expected
    assert return_code == 1


def test_main_add_header_to_executable_file(tmp_path):
    license_file = tmp_path.joinpath('license')
    license_file.write_text(
        'TEST LICENSE\n'
        'this is a test license\n'
        '${start_year}\n'
        '${end_year}\n'
        '${author_name}\n',
    )
    f = tmp_path.joinpath('t.py')
    f.write_text(
        '#!/usr/bin/env python3\n'
        'print("Hello World")\n',
    )

    return_code = main([
        '--license', license_file.resolve().as_posix(),
        '--start-year', '2023',
        '--end-year', '2024',
        '--author-name', 'John Smith',
        f.resolve().as_posix(),
    ])

    expected = """\
#!/usr/bin/env python3

# LICENSE HEADER MANAGED BY add-license-header
#
# TEST LICENSE
# this is a test license
# 2023
# 2024
# John Smith

print("Hello World")
"""
    assert f.read_text() == expected
    assert return_code == 1


def test_main_no_change(tmp_path):
    license_file = tmp_path.joinpath('license')
    license_file.write_text(
        'TEST LICENSE\n'
        'this is a test license\n'
        '${start_year}\n'
        '${end_year}\n'
        '${author_name}\n',
    )
    f = tmp_path.joinpath('t.py')
    f.write_text(
        '# LICENSE HEADER MANAGED BY add-license-header\n'
        '#\n'
        '# TEST LICENSE\n'
        '# this is a test license\n'
        '# 2023\n'
        '# 2024\n'
        '# John Smith\n'
        '\n'
        'print("Hello World")\n',
    )

    return_code = main([
        '--license', license_file.resolve().as_posix(),
        '--start-year', '2023',
        '--end-year', '2024',
        '--author-name', 'John Smith',
        f.resolve().as_posix(),
    ])

    expected = """\
# LICENSE HEADER MANAGED BY add-license-header
#
# TEST LICENSE
# this is a test license
# 2023
# 2024
# John Smith

print("Hello World")
"""
    assert f.read_text() == expected
    assert return_code == 0


def test_main_check_mode(tmp_path):
    license_file = tmp_path.joinpath('license')
    license_file.write_text(
        'TEST LICENSE\n'
        'this is a test license\n'
        '${start_year}\n'
        '${end_year}\n'
        '${author_name}\n',
    )
    f = tmp_path.joinpath('t.py')
    f.write_text('print("Hello World")\n')

    return_code = main([
        '--license', license_file.resolve().as_posix(),
        '--start-year', '2023',
        '--end-year', '2024',
        '--author-name', 'John Smith',
        '--check',
        f.resolve().as_posix(),
    ])

    assert f.read_text() == 'print("Hello World")\n'
    assert return_code == 1


def test_main_unknown_file_type(tmp_path):
    license_file = tmp_path.joinpath('license')
    license_file.write_text(
        'TEST LICENSE\n'
        'this is a test license\n'
        '${start_year}\n'
        '${end_year}\n'
        '${author_name}\n',
    )
    f = tmp_path.joinpath('unsupported')
    f.write_text('unsupported')

    return_code = main([
        '--license', license_file.resolve().as_posix(),
        '--start-year', '2023',
        '--end-year', '2024',
        '--author-name', 'John Smith',
        '--check',
        f.resolve().as_posix(),
    ])

    assert return_code == -1


def test_main_binary_file(tmp_path):
    license_file = tmp_path.joinpath('license')
    license_file.write_text(
        'TEST LICENSE\n'
        'this is a test license\n'
        '${start_year}\n'
        '${end_year}\n'
        '${author_name}\n',
    )
    f = tmp_path.joinpath('t.exe')
    f.write_text('binary file')

    return_code = main([
        '--license', license_file.resolve().as_posix(),
        '--start-year', '2023',
        '--end-year', '2024',
        '--author-name', 'John Smith',
        '--check',
        f.resolve().as_posix(),
    ])

    assert return_code == -1
