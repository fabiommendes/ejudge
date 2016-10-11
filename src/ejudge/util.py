import contextlib
import io
import os
import sys
import signal
import traceback
from threading import Thread


#
# Special IO functions for python script interactions
#
from iospec import datatypes

_print_func = print
_stdout = sys.stdout


def real_print(*args, **kwargs):
    """Print function for the C's stdout."""

    kwargs.setdefault('file', _stdout)
    _print_func(*args, **kwargs)


def capture_print(*args, **kwds):
    """A print-like function that return the formatted string instead of
    printing it on screen"""

    out, err = sys.stdout, sys.stderr
    out_io = sys.stdout = sys.stderr = io.StringIO()
    try:
        _print_func(*args, **kwds)
    finally:
        sys.stdout, sys.stderr = out, err
    return out_io.getvalue()


#
# Execution with time limits
#
def __timeout_handler(signum, frame):
    """Helper function for the timeout() function."""

    raise TimeoutError()


def timeout(func, args=(), kwargs={}, timeout=1.0, threading=True):
    """
    Execute callable `func` with timeout. If timeout is None or zero,
    ignores any timeout exceptions.

    If timeout exceeds, raises a TimeoutError.
    """

    if timeout is not None and timeout <= 0:
        raise ValueError('timeout must be positive')

    if not timeout or not 1 / timeout:
        return func(*args, **kwargs)

    if threading:
        result = []
        exceptions = []

        def target():
            try:
                result.append(func(*args, **kwargs))
            except Exception as ex:
                exceptions.append(ex)

        thread = Thread(target=target, daemon=True)
        thread.start()
        thread.join(timeout=timeout)
        if thread.is_alive():
            raise TimeoutError
        else:
            try:
                return result.pop()
            except IndexError:
                raise exceptions.pop()
    else:
        signal.signal(signal.SIGALRM, __timeout_handler)
        signal.alarm(timeout)
        try:
            result = func(*args, **kwargs)
        finally:
            signal.alarm(0)

        return result


#
# Lazy evaluation
#
class lazy(object):
    """
    Lazy accessor.
    """

    def __init__(self, func):
        self.func = func

    def __get__(self, obj, cls=None):
        if obj is None:
            return self
        value = self.func(obj)
        setattr(obj, self.func.__name__, value)
        return value


class pushbackiter:
    """A simple push back iterator: push()'d items are restored to iteration.

    Example
    -------

    >>> it = pushbackiter([1, 2, 3]);
    >>> it.push(0); list(it)
    [0, 1, 2, 3]
    """

    def __init__(self, it):
        self.iter = iter(it)
        self.buffer = []

    def __iter__(self):
        return self

    def __next__(self):
        buffer = self.buffer
        while buffer:
            return buffer.pop()
        return next(self.iter)

    def push(self, value):
        """Send a value to the beginning of iteration."""

        self.buffer.append(value)


@contextlib.contextmanager
def keep_cwd():
    """
    Context manager that restores the cwd at the beginning of execution when it
    exits the with block."""

    currpath = os.getcwd()
    yield
    os.chdir(currpath)


@contextlib.contextmanager
def do_nothing_context_manager():
    """
    A do-nothing context manager.
    """
    yield


def remove_trailing_newline_from_testcase(case):
    """
    Remove a trailing newline from the last output node.
    """

    if case is None:
        return None

    if case:
        last = case[-1]
        if isinstance(last, datatypes.Out) and last.endswith('\n'):
            last.data = str(last[:-1])
    return case


def format_traceback(ex, source):
    """
    Creates a error message string from an exception with a __traceback__
    value. Usually this requires that this function must be executed inside
    the except block that caught the exception.
    """

    ex_name = type(ex).__name__
    messages = []
    code_lines = source.splitlines()
    tb = ex.__traceback__

    tb_list = reversed(traceback.extract_tb(tb))
    for (filename, lineno, func_name, text) in tb_list:
        if 'ejudge' in filename:
            break
        if filename == '<string>':
            text = code_lines[lineno - 1].strip()
        messages.append((filename, lineno, func_name, text))

    messages.reverse()
    messages = traceback.format_list(messages)
    messages.insert(0, 'Traceback (most recent call last)')
    messages.append('%s: %s' % (ex_name, ex))
    return '\n'.join(messages)
