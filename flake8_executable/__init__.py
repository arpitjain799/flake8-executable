# Copyright (c) 2019 Hong Xu <hong@topbug.net>

# This file is part of flake8-executable.

# flake8-executable is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.

# flake8-executable is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License
# for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with flake8-executable. If not, see <https://www.gnu.org/licenses/>.

from abc import ABC
import os

from .version import __version__


class Error(ABC):
    "Base class of all errors."

    def __init__(self, line_number, offset, error_code, message, check):
        self.line_number = line_number
        self.offset = offset
        self.error_code = error_code
        self.message = message
        self.check = check

    @staticmethod
    def format_flake8(line_number, error_code, offset, message, check):
        "Return a format of that Flake8 accepts."
        return line_number, offset, '{} {}'.format(error_code, message), check

    def __call__(self, **kwargs):
        """Return a format of this error that Flake8 accepts. Override this method to incorporate variables, such as line
        numbers, during runtime.
        """
        return __class__.format_flake8(self.line_number, self.error_code, self.offset, self.message, self.check)

    def should_check(self, **kwargs) -> bool:
        "Whether this error should be checked."
        return True


class EXE001(Error):
    def __init__(self):
        super().__init__(0, 0, 'EXE001', 'Shebang is present but the file is not executable.', '')

    def should_check(self, filename, **kwargs) -> bool:
        # Do not check on Windows or the input is not a file in the filesystem.
        return os.name != 'nt' and filename is not None and filename != '-'


exe001 = EXE001()


class EXE002(Error):
    def __init__(self):
        super().__init__(0, 0, 'EXE002', 'The file is executable but no shebang is present.', '')

    def should_check(self, filename, **kwargs) -> bool:
        # Do not check on Windows or the input is not a file in the filesystem.
        return os.name != 'nt' and filename is not None and filename != '-'


exe002 = EXE002()


class EXE003(Error):
    def __init__(self):
        super().__init__(0, 0, 'EXE003', 'Shebang is present but does not contain "python"', '')

    def __call__(self, shebang, **kwargs):
        return __class__.format_flake8(self.line_number, self.error_code, self.offset,
                                       '{}: {}'.format(self.message, shebang), self.check)


exe003 = EXE003()


class ExecutableChecker:
    name = 'flake8-executable'
    version = __version__

    def __init__(self, tree=None, filename=None, lines=None):
        self.filename = filename
        self.lines = lines

    def run(self):
        # Get first line
        if self.lines:
            first_line = self.lines[0]
        else:
            with open(self.filename) as f:
                first_line = f.readline()

        has_shebang = first_line.startswith('#!')
        is_executable = os.access(self.filename, os.X_OK)
        if has_shebang:
            if not is_executable:
                if exe001.should_check(filename=self.filename):
                    yield exe001()
            if 'python' not in first_line:
                if exe003.should_check():
                    yield exe003(first_line.strip())
        elif not has_shebang and is_executable:
            # In principle, this error may also be yielded on empty
            # files, but flake8 seems to always skip empty files.
            if exe002.should_check(filename=self.filename):
                yield exe002()
