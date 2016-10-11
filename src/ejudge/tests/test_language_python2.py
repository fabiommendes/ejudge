import pytest

from ejudge import functions
from ejudge.tests import abstract as base

sources = r"""
## ok
name = raw_input("name: ")
print "hello %s!" % name

## wrong
name = raw_input("name: ")
print(name)

## syntax
a b

## error
1 / 0

## recursive
def f(x):
    return 1 if x <= 1 else x * f(x - 1)
print(f(5))
"""


@pytest.mark.python2
class TestPython2Support(base.TestLanguageSupport):
    base_lang = 'python2'
    source_all = sources

    @pytest.mark.skip
    def test_error_feedback_message_shows_traceback(self, lang, iospec):
        iospec = functions.run('1 / 0', ['foo'], lang=lang, sandbox=False)
        assert iospec[0].error_message == (
            'Traceback (most recent call last)\n'
            '  File "main.py", line 1, in <module>\n'
            'ZeroDivisionError: division by zero'
        )
