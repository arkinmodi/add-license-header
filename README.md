# add-license-header

A tool for automatically adding your license as a header in your source code.

## Installation

```bash
pip install add-license-header
```

## pre-commit hook

See [pre-commit](https://github.com/pre-commit/pre-commit) for instructions.

Sample with license template file:

```yaml
- repo: https://github.com/arkinmodi/add-license-header
  rev: v2.0.1
  hooks:
      - id: add-license-header
        args:
            - --license-file
            - MIT-LICENSE.template
```

Sample with inline license template:

```yaml
- repo: https://github.com/arkinmodi/add-license-header
  rev: v2.0.1
  hooks:
      - id: add-license-header
        args:
            - --license
            - |
                MIT License

                Copyright (c) $create_year $author_name
                ...
```

## Template Options

You can use template markers to dynamically change your license.

|  Template Marker  |                                   Default                                    |      CLI Flag      |
| :---------------: | :--------------------------------------------------------------------------: | :----------------: |
|  `$author_name`   |                                Empty string.                                 |  `--author-name`   |
|  `$create_year`   | Introduction into git history. If not managed by git, then the current year. |  `--create-year`   |
|   `$edit_year`    |                                Current year.                                 |   `--edit-year`    |
| `$year_delimiter` |                                     ", "                                     | `--year-delimiter` |

For example:

```text
MIT License

Copyright (c) $create_year $author_name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## What does it do?

```shell
$ cat example.py
print("Hello World")

$ add-license-header \
    --license-file MIT-LICENSE.template \
    --author-name 'Arkin Modi' \
    --create-year 2023 \
    example.py
updating license in example.py

$ cat example.py
# LICENSE HEADER MANAGED BY add-license-header
#
# MIT License
#
# Copyright (c) 2023 Arkin Modi
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

print("Hello World")
```

## Managed vs Un-Managed

In managed mode (the default), the license header will contain
`LICENSE HEADER MANAGED BY add-license-header` in first line of the comment
block. This enabled the tool to be able to accurately find the license header
and allows you to place the license header anywhere in the file.

In unmanaged mode, enabled with the `--unmanaged` flag, the top-most comment
block will be assumed to be the license header.
