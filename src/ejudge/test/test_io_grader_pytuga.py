import pytest
from iospec import parse_string, types
from ejudge import io
from ejudge.test.test_io_grader_python import (
    iospec,
    test_run_ok,
    test_run_ok_with_timeout,
    test_run_ok_with_sandbox,
    test_run_ok_with_sandbox_and_timeout,
    test_grade_correct,
    test_grade_wrong,
)


@pytest.fixture
def src_ok():
    return (
        'nome = leia_texto("name: ")\n'
        'mostre("hello %s!" % nome)')


@pytest.fixture
def src_bad():
    return (
        'nome = leia_texto("name: ")\n'
        'mostre("hello %s." % nome)')


@pytest.fixture
def lang():
    return 'pytuga'


def test_pytuga_keeps_a_clean_environment(src_ok):
    io.run(src_ok, ['tuga'], lang='pytuga', sandbox=False)
    assert str(True) == 'True'


if __name__ == '__main__':
    pytest.main('test_io_grader_pytuga.py')
