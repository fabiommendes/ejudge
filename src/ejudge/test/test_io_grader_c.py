import pytest
from ejudge import io
from iospec import parse_string, types
from ejudge.test.test_io_grader_python import (
    iospec,
    test_run_ok,
    test_run_ok_with_timeout,
    test_run_ok_with_sandbox,
    test_run_ok_with_sandbox_and_timeout,
)


@pytest.fixture
def lang():
    return 'gcc'


@pytest.fixture
def src_ok():
    return r"""
#include<stdio.h>

void main() {
    char buffer[100];
    printf("name: ");
    scanf("%s", buffer);
    printf("hello %s!\n", buffer);
}
"""


@pytest.fixture
def src_bad():
    return """
#include<stdio.h>

void main() {
    char buffer[100];
    puts("name: ");
    scanf("%s", buffer);
    printf("%s\n", buffer);
}
"""

if __name__ == '__main__':
    pytest.main('test_io_grader_c.py')
