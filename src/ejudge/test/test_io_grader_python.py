from pprint import pprint
import pytest
from ejudge import io
from iospec import parse_string, types


@pytest.fixture
def iospec():
    return parse_string(
        'name: <foo>\n'
        'hello foo!\n'
        '\n'
        'name: <bar>\n'
        'hello bar!')


@pytest.fixture
def lang():
    return 'python'


@pytest.fixture
def src_ok():
    return (
        'name = input("name: ")\n'
        'print("hello %s!" % name)')


@pytest.fixture
def src_bad():
    return (
        'name = input("name: ")\n'
        'print(name)')


#
# Test simple io.run() interactions
#
def test_run_ok(src_ok, lang, timeout=None, sandbox=False):
    tree = io.run(src_ok, ['foo'], lang=lang, sandbox=sandbox, timeout=timeout)
    case = tree[0]
    tree.pprint()
    assert tree
    assert len(tree) == 1
    assert case[0] == 'name: '
    assert case[1] == 'foo'
    assert case[2] == 'hello foo!'


def test_run_ok_with_timeout(src_ok, lang):
    test_run_ok(src_ok, lang, timeout=1.0)


def test_run_ok_with_sandbox(src_ok, lang):
    test_run_ok(src_ok, lang, sandbox=True)


def test_run_ok_with_sandbox_and_timeout(src_ok, lang):
    test_run_ok(src_ok, lang, sandbox=True, timeout=1.0)


#
# Test io.grade() and check if the feedback is correct
#
def test_grade_correct(iospec, src_ok, lang):
    feedback = io.grade(src_ok, iospec, lang=lang, sandbox=False)
    assert isinstance(feedback.answer_key, types.TestCase)
    assert isinstance(feedback.case, types.TestCase)
    assert feedback.grade == 1
    assert feedback.message is None
    assert feedback.status == 'ok'


def test_grade_wrong(iospec, src_bad, lang):
    feedback = io.grade(src_bad, iospec, lang=lang, sandbox=False)
    assert feedback.grade == 0
    assert feedback.status == 'wrong-answer'
    assert feedback.title == 'Wrong Answer'


def test_run_from_input_sequence(src_ok, lang):
    tree = io.run(src_ok, [['foo'], ['bar']], lang=lang, sandbox=False)
    assert len(tree) == 2
    assert tree[0][2] == 'hello foo!'
    assert tree[1][2] == 'hello bar!'


def test_run_from_iospec_input(src_ok, lang):
    case1 = types.IoTestCase([types.In('foo'), types.Out('foo')])
    case2 = types.InputTestCase([types.In('bar')])
    inpt = types.IoSpec([case1, case2])
    tree = io.run(src_ok, inpt, lang=lang, sandbox=False)
    assert len(tree) == 2
    assert tree[0][2] == 'hello foo!'
    assert tree[1][2] == 'hello bar!'



if __name__ == '__main__':
    pytest.main([__file__])
