import pytest
from ejudge import io
from iospec import parse_string, types


#
# Prevent regressions by registering specific interaction bugs
#
def test_less_inputs_than_expected(lang='python', sandbox=False):
    src = 'print(42)'
    iosrc = 'foo<42>\nbar<0>\n42'
    fb = io.grade(src, iosrc, lang=lang, sandbox=sandbox)
    fb.case.pprint()
    fb.answer_key.pprint()
    assert fb.grade == 0
    assert fb.status == 'wrong-answer'


def test_less_inputs_than_expected_sandbox():
    test_less_inputs_than_expected(sandbox=True)


def test_less_inputs_than_expected_pytuga():
    test_less_inputs_than_expected(lang='python3')


if __name__ == '__main__':
    pytest.main('test_examples.py')
