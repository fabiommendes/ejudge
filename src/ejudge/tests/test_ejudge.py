import pytest
import ejudge


def test_project_defines_author_and_version():
    assert hasattr(ejudge, '__author__')
    assert hasattr(ejudge, '__version__')
