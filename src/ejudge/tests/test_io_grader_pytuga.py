import pytest
from ejudge import functions
from ejudge.tests.test_io_grader_python import (
    iospec,
    test_run_valid_source,
    test_run_valid_source_with_timeout,
    test_run_valid_source_with_sandbox,
    test_run_valid_source_with_sandbox_and_timeout,
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
    functions.run(src_ok, ['tuga'], lang='pytuga', sandbox=False)
    assert str(True) == 'True'
