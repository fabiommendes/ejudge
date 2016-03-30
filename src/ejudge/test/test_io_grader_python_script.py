import pytest
from iospec import parse_string, iotypes
from ejudge import io
from ejudge.contrib import pytuga_language
from ejudge.test.test_io_grader_python import (
    iospec,
    test_run_ok,
    test_run_ok_with_timeout,
    test_run_ok_with_sandbox,
    test_run_ok_with_sandbox_and_timeout,
    test_grade_correct,
    test_grade_wrong,
    src_ok,
    src_bad
)


@pytest.fixture
def lang():
    return 'python3'


if __name__ == '__main__':
    pytest.main('test_io_grader_python_script.py')
