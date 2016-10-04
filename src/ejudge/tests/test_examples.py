import pytest

import iospec
from ejudge import functions

simple_inputs = """
<foo>
<bar>
<baz>
foo bar baz
"""

simple_source = """
x, y, z = input(), input(), input()
print(x, y, z)
"""


# Program uses less inputs than predicted on iospec file
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


# Simple inputs with out the corresponding output interaction
def test_simple_inputs():
    ast = iospec.parse(simple_inputs)
    ast.normalize()
    result = functions.run(simple_source, ast, lang='python')
    result.normalize()
    ast.pprint()
    result.pprint()
    assert ast.to_json() == result.to_json()
    assert iospec.isequal(ast, result)


def test_grade_simple_inputs():
    ast = iospec.parse(simple_inputs)
    feedback = functions.grade(simple_source, ast, lang='python')
    assert feedback.grade == 1
