from pprint import pprint
import pytest
from ejudge import functions
from iospec import parse_string, types, SimpleTestCase


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
        'print("hello %s!" % name)'
    )


@pytest.fixture
def src_bad():
    return (
        'name = input("name: ")\n'
        'print(name)'
    )


#
# Test simple io.run() interactions
#
def test_run_valid_source(src_ok, lang, timeout=None, sandbox=False):
    tree = functions.run(src_ok, ['foo'], lang=lang, sandbox=sandbox, timeout=timeout,
                         raises=True)
    try:
        assert len(tree) == 1
        case = tree[0]
        assert isinstance(case, SimpleTestCase)
        assert case[0] == 'name: '
        assert case[1] == 'foo'
        assert case[2] == 'hello foo!'
    except Exception:
        tree.pprint()
        raise


def test_run_valid_source_with_timeout(src_ok, lang):
    test_run_valid_source(src_ok, lang, timeout=1.0)


@pytest.mark.slow
def test_run_valid_source_with_sandbox(src_ok, lang):
    test_run_valid_source(src_ok, lang, sandbox=True)


@pytest.mark.slow
def test_run_valid_source_with_sandbox_and_timeout(src_ok, lang):
    test_run_valid_source(src_ok, lang, sandbox=True, timeout=1.0)


#
# Test io.grade() and check if the feedback is correct
#
def test_grade_correct(iospec, src_ok, lang):
    feedback = functions.grade(src_ok, iospec, lang=lang, sandbox=False)
    assert isinstance(feedback.answer_key, types.TestCase)
    assert isinstance(feedback.testcase, types.TestCase)
    assert feedback.grade == 1
    assert feedback.message is None
    assert feedback.status == 'ok'


def test_grade_wrong(iospec, src_bad, lang):
    feedback = functions.grade(src_bad, iospec, lang=lang, sandbox=False)
    assert feedback.grade == 0
    assert feedback.status == 'wrong-answer'
    assert feedback.title == 'Wrong Answer'


def test_run_from_input_sequence(src_ok, lang):
    tree = functions.run(src_ok, [['foo'], ['bar']], lang=lang, sandbox=False)
    assert len(tree) == 2
    assert tree[0][2] == 'hello foo!'
    assert tree[1][2] == 'hello bar!'


def test_run_from_iospec_input(src_ok, lang):
    case1 = types.SimpleTestCase([types.In('foo'), types.Out('foo')])
    case2 = types.InputTestCase([types.In('bar')])
    inpt = types.IoSpec ([case1, case2])
    tree = functions.run(src_ok, inpt, lang=lang, sandbox=False)
    assert len(tree) == 2
    assert tree[0][2] == 'hello foo!'
    assert tree[1][2] == 'hello bar!'


def test_run_code_with_runtime_error():
    tree = functions.run('1/0', ['foo'], lang='python', sandbox=False)
    lines = tree[0].error_message.splitlines()
    assert lines[0] == 'Traceback (most recent call last)'
    assert lines[1].startswith('  File ')
    assert lines[-1].startswith('ZeroDivisionError')


def test_run_code_with_syntax_error():
    tree = functions.run('bad syntax', ['foo'], lang='python', sandbox=False)
    assert len(tree) == 1
    assert isinstance(tree[0], types.ErrorTestCase)
    # assert tree[0].error_message == (
    #     'Traceback (most recent call last)\n'
    #     '  File "main.py", line 1\n'
    #     '    bad syntax\n'
    #     '             ^\n'
    #     'SyntaxError: invalid syntax\n')
    # assert 'bad syntax' in tree[0].error_message


def test_grade_with_runtime_error():
    iospec = parse_string('foo<bar>\nfoobar')
    feedback = functions.grade('1/0', iospec, lang='python', sandbox=False)
    assert feedback.grade == 0
    assert feedback.title == 'Runtime Error'
    assert feedback.testcase.error_message == (
        'Traceback (most recent call last)\n'
        '  File "main.py", line 1, in <module>\n\n'
        'ZeroDivisionError: division by zero')


def test_run_recursive_function():
    src = '''
def f(x):
    return 1 if x <= 1 else x * f(x - 1)
print(f(5))
'''
    result = functions.run(src, [()], lang='python', sandbox=False)
    assert list(result[0]) == ['120']


def test_run_recursive_function_in_sandbox():
    src = '''
def f(x):
    return 1 if x <= 1 else x * f(x - 1)
print(f(5))
'''
    result = functions.run(src, [()], lang='python', sandbox=True)
    assert list(result[0]) == ['120']

