import pytest
from ejudge import functions
from iospec import parse_string, types
from ejudge.tests.test_io_grader_python import (
    iospec,
    test_run_valid_source,
    test_run_valid_source_with_timeout,
    test_run_valid_source_with_sandbox,
    test_run_valid_source_with_sandbox_and_timeout,
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
    return r"""
#include<stdio.h>

void main() {
    char buffer[100];
    puts("name: ");
    scanf("%s", buffer);
    printf("%s\n", buffer);
}
"""


def test_c_program_with_two_inputs():
    src = r"""
#include<stdio.h>

void main() {
    char name[100], job[200];
    printf("name: ");
    scanf("%s", name);
    printf("job: ");
    scanf("%s", job);
    printf("%s, %s\n", name, job);
}
"""
    result = functions.run(src, ['foo', 'bar'], lang='c', sandbox=False)
    case = result[0]
    print(case)
    result.pprint()
    assert list(case) == ['name: ', 'foo', 'job: ', 'bar', 'foo, bar']
