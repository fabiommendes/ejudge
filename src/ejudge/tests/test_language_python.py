import pytest
import time

from ejudge import functions
from ejudge.tests import abstract as base

sources = r"""
## ok
name = input("name: ")
print("hello %s!" % name)


## wrong
name = input("name: ")
print(name)


## syntax
a b


## error
1 / 0


## recursive
def f(x):
    return 1 if x <= 1 else x * f(x - 1)
print(f(5))


## timeout
import time

name = input('name: ')
t0 = time.time()

# semi-infinite loop :)
while time.time() < t0 + 0.5:
    pass
"""


@pytest.mark.python
class TestPythonSupport(base.TestLanguageSupport):
    base_lang = 'python'
    source_all = sources

    def test_error_feedback_message_shows_traceback(self, lang, iospec):
        feedback = functions.grade('1 / 0', iospec, lang=lang, sandbox=False)
        assert feedback.grade == 0
        assert feedback.title == 'Runtime Error'
        assert feedback.testcase.error_message == (
            'Traceback (most recent call last)\n'
            '  File "main.py", line 1, in <module>\n\n'
            'ZeroDivisionError: division by zero')

    def test_raises_timeout_error(self, lang, iospec):
        src = self.get_source('timeout')
        t0 = time.time()
        result = functions.run(src, iospec, lang=lang, timeout=0.1, sandbox=False)
        dt = time.time() - t0
        assert result.get_error_type() == 'timeout'
        assert dt < 0.45  # slightly less than maximum program runtime

    @pytest.mark.sandbox
    def test_raises_timeout_error_in_sandbox(self, lang, iospec):
        src = self.get_source('timeout')
        result = functions.run(src, iospec, lang=lang, timeout=0.05, sandbox=True)
        assert result.get_error_type() == 'timeout'
