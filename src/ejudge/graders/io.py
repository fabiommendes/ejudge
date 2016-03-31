import decimal
import functools
import io
import os
import traceback
import boxed
from ejudge import util
from ejudge.langs import BuildError, manager_from_lang, lang_from_extension
from iospec import iotypes, parse_string
from iospec.feedback import get_feedback
from iospec.iotypes import TestCase

# Python print function using the standard stdout
__all__ = ['grade', 'run', 'BuildError']
grade = run = None


def build_and_run(func, args, kwds, manager, timeout, raises):
    # Build
    try:
        manager.build()
    except BuildError as ex:
        if raises:
            raise
        return func(*args, build_error=(ex, ex.__traceback__))

    # Run task
    args += (manager,)
    if timeout:
        return util.timeout(func, args=args, kwargs=kwds, timeout=timeout)
    else:
        return func(*args, **kwds)


def prepare_manager(func):
    """Decorate functions in this block to receive a configured manager"""

    @functools.wraps(func)
    def decorated(src, *args, path=None, lang=None, manager=None, raises=True,
                  sandbox=False, timeout=None, **kwds):
        # Fix language
        if manager is None:
            if lang is None:
                ext = os.path.splitext(path or src.name)[1] or '.'
                try:
                    lang = lang_from_extension(ext)
                except KeyError:
                    raise ValueError('unknown extension: %r' % ext)

            # Normalize source string
            if not isinstance(src, str):
                src = src.read()
            manager = manager_from_lang(lang, src)

        # Sandbox build and running phases
        manager.is_sandboxed = sandbox
        args = (func, args, kwds, manager, timeout, raises)
        with manager.keep_cwd():
            if sandbox:
                imports = manager.modules()
                result = boxed.run(build_and_run, args=args, imports=imports)
            else:
                result = build_and_run(*args)
        return result

    globals()[func.__name__[1:]] = decorated
    return func


# noinspection PyUnresolvedReferences
@prepare_manager
def _grade(iospec, manager, fast=True, build_error=None):
    """
    Grade the string of source code by comparing the results of all inputs and
    outputs in the given template structure.


    Parameters
    ----------

    src : str or file object
        The source string for the code or a file object
    iospec : IOSpec parse tree
        The expected template for correct answers
    lang : str
        Programming language for the given source code. The judge accepts the
        following languages. Users can register plugins to support additional
        languages or to override the default behavior or accepted languages.

        +===========+==========================================================+
        | Value     | Description                                              |
        +===========+==========================================================+
        | python    | For Python 3.x code. Default runner.                     |
        +-----------+----------------------------------------------------------+
        | python2   | Executes in a separate Python 2 interpreter.             |
        +-----------+----------------------------------------------------------+
        | python3   | Executes in a separate Python 3 interpreter. Used mostly |
        |           | for debuging since it lack in features and performance   |
        |           | compared to the default "python" runner.                 |
        +-----------+----------------------------------------------------------+
        | tcc       | Compile C code with the tiny C compiler                  |
        +-----------+----------------------------------------------------------+
        | clang     | Compile C code with clang                                |
        +-----------+----------------------------------------------------------+
        | gcc       | Compile C code with gcc                                  |
        +-----------+----------------------------------------------------------+
        | C         | Uses the first method available: tcc, clang or gcc       |
        +-----------+----------------------------------------------------------+

    sandbox : bool
        If True, code will run in a sandboxed environment as the `nobody` user.
        It is necessary to have your system properly configured in order to do
        this.
    timeout : float
        Maximum time (in seconds) for the complete test to run.

    Specific backends may support additional keyword arguments. The most common
    ones are shown bellow

    namespace (python): dict
        The globals() namespace used to run a python script.


    Returns
    -------

    A named tuple of (grade, feedback) with a decimal grade normalized to 1 and
    None or a feedback structure.
    """

    if build_error:
        ex, tb = build_error
        case = build_error_test_case(ex, tb)
        return get_feedback(case, iospec)

    if isinstance(iospec, str):
        iospec = parse_string(iospec)
    if not iospec:
        raise ValueError('cannot grade an iospec that has no cases')

    value = decimal.Decimal(1)
    feedback = None

    for answer_key in iospec:
        inputs = answer_key.inputs()
        case = manager.run(inputs)
        if not isinstance(case, TestCase):
            raise RuntimeError(
                'Manager %s .run() method did not return a TestCase: got a %s '
                'instance' % (type(manager).__name__, type(case).__name__),
            )

        curr_feedback = get_feedback(case, answer_key)

        if feedback is None:
            feedback = curr_feedback

        if curr_feedback.grade < value:
            feedback = curr_feedback
            value = curr_feedback.grade

            if value == 0 and fast:
                break

    return feedback


# noinspection PyUnresolvedReferences
@prepare_manager
def _run(inputs, manager=None, build_error=None):

    """Runs program with the given list of inputs and returns the
    corresponding IoSpecTree.

    Parameters
    ----------

    src : str or file
        The source code for the test program
    inputs : sequence
        A sequence of input strings. If input is a sequence of sequences,
        this function will perform multiple test cases.
    lang : str
        The name for the source code language. See :func:`ejudge.graders.io.grade`
        for more details.
    timeout : float
        A time limit for the entire run (in seconds). If this attribute is not
        given, the program will run without any timeout. This can be potentially
        dangerous if the input program has an infinite loop.
    sandbox : bool
        Controls if code is run in sandboxed mode or not. Sandbox protection
        is the default behavior on supported platforms.
    raises : bool
        If True, raise a BuildError if the build process fails. The default
        behavior is to return a IoSpecTree with a single test case of type
        'error-build'.
    path : str
        The absolute file path for the input string or file object.

    Returns
    -------

    A :cls:`iospec.IoSpecTree structure. If inputs is a sequence of strings,
    the resulting tree will have a single test case in its "cases" attribute.
    """

    if build_error:
        result = iotypes.IoSpec(build_error_test_case(*build_error))
    else:
        inputs = util.pushbackiter(inputs)
        first = next(inputs)
        inputs.push(first)

        if isinstance(first, str):
            cases = [manager.run(inputs)]
        else:
            cases = [manager.run(values) for values in inputs]
        result = iotypes.IoSpec(cases)

    #result.setmeta('context', manager.context)
    result.setmeta('lang', manager.name)
    result.setmeta('buildargs', manager.buildargs)
    result.setmeta('shellargs', manager.shellargs)
    return result


def build_error_test_case(ex, tb):
    out = io.StringIO()
    traceback.print_tb(tb, file=out)

    return iotypes.ErrorTestCase.build(error_message=out.getvalue())
