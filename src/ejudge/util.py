import io
import sys
import signal
from threading import Thread


#
# Special IO functions for python script interactions
#
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


def timeout(func, args=(), kwargs={}, timeout=1.0, threading=True,
            raises=True):
    """Execute callable `func` with timeout. If timeout is None or zero,
    ignores any timeout exceptions.

    If timeout exceeds, raises a TimeoutError"""

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

        thread = Thread(target=target)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            if raises:
                raise TimeoutError
            else:
                return None
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
        except TimeoutError:
            if raises:
                raise
            else:
                return None
        finally:
            signal.alarm(0)

        return result


#
# Lazy evaluation
#
class lazy(object):
    """Lazy accessor"""

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


if __name__ == '__main__':
    from doctest import testmod
    testmod()