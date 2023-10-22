# add-license-header

A tool for automatically adding your license as a header in your source code.

## Template Options

You can use template markers to dynamically change your license.

| Template Marker  |   Default    |    CLI Flag     |
| :--------------: | :----------: | :-------------: |
| `${start_year}`  | Current Year | `--start-year`  |
|  `${end_year}`   | Current Year |  `--end-year`   |
| `${author_name}` | Empty String | `--author-name` |

For example:

```text
MIT License

Copyright (c) ${start_year} ${author_name}

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
    --license MIT-LICENSE.template \
    --author 'Arkin Modi' \
    --start-year 2023 \
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

print("Hello World")
```

## Configuration File

Instead of always using the CLI flags, you can define them in a JSON file. CLI
flags will have higher priority than the configuration file. None of the fields
are required (except `license` which must be defined with in the configuration
file or using the CLI flag, `--license`).

The default configuration file name is `.add-license-header.json` in the working
directory. A custom path can be specified with the `--config-file` CLI flag.

Here is the schema of the configuration:

```json
{
    "author_name": "name of author or organization",
    "end_year": "end year (number or string)",
    "license": "path to license file",
    "start_year": "start year (number or string)"
}
```
