import pytest
from ejudge import functions
from iospec import parse, types


#
# Prevent regressions by registering specific interaction bugs
#
def test_less_inputs_than_expected(lang='python', sandbox=False):
    src = 'print(42)'
    iosrc = (
        'foo<42>\n'
        'bar<0>\n'
        '42'
    )
    fb = functions.grade(src, iosrc, lang=lang, sandbox=sandbox)
    fb.testcase.pprint()
    fb.answer_key.pprint()
    assert fb.grade == 0
    assert fb.status == 'wrong-answer'


@pytest.mark.sandbox
def test_less_inputs_than_expected_sandbox():
    test_less_inputs_than_expected(sandbox=True)


def test_less_inputs_than_expected_pytuga():
    test_less_inputs_than_expected(lang='pytuga')
