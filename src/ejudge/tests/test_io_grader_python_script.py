import pytest
from iospec import parse_string, types
from ejudge import functions
from ejudge.tests.test_io_grader_python import (
    iospec,
    test_run_valid_source,
    test_run_valid_source_with_timeout,
    test_run_valid_source_with_sandbox,
    test_run_valid_source_with_sandbox_and_timeout,
    test_grade_correct,
    test_grade_wrong,
    src_ok,
    src_bad
)


@pytest.fixture
def lang():
    return 'python-script'
