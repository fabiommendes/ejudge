import decimal
import io
import os
import traceback
from boxed.jsonbox import run as run_sandbox
from iospec import parse_string, TestCase, ErrorTestCase, IoSpec
from iospec.feedback import feedback as get_feedback, Feedback
from ejudge.langs import BuildError, manager_from_lang, lang_from_extension
from ejudge.util import real_print


# Python print function using the standard stdout
__all__ = ['grade', 'run', 'BuildError']


def run(source, inputs, lang=None, *,
        timeout=None, raises=False, path=None, sandbox=True):
    """Run program with the given list of inputs and returns the
    corresponding :cls:`iospec.IoSpec` instance.

    Parameters
    ----------

    source : str or file
        The source code for the test program
    inputs : sequence
        A sequence of input strings. If input is a sequence of sequences,
        this function will perform multiple test cases. It can also be a IoSpec
        or a TestCase instance which are used to extract the necessary input
        strings.
    lang : str
        The name for the source code language. See
        :func:`ejudge.graders.io.grade` for more details.
    timeout : float
        A time limit for the entire run (in seconds). If this attribute is not
        given, the program will run without any timeout. This can be potentially
        dangerous if the input program has an infinite loop.
    sandbox : bool
        Controls if code is run in sandboxed mode or not. Sandbox protection
        is the default behavior on supported platforms.
    raises : bool
        If True, raise a BuildError if the build process fails. The default
        behavior is to return a IoSpec instance with a single ErrorTestCase with
        a type string of 'error-build'.
    path : str
        The absolute file path for the input string or file object.

    Returns
    -------

    A :cls:`iospec.IoSpec` structure. If ``inputs`` is a sequence of strings,
    the resulting tree will have a single test case.
    """

    manager = get_manager(lang, source, path)
    manager.is_sandboxed = sandbox

    # Normalize inputs
    if isinstance(inputs, (IoSpec, TestCase)):
        inputs = inputs.inputs()
    else:
        if isinstance(inputs[0], str):
            inputs = [list(inputs)]
        else:
            inputs = [list(x) for x in inputs]

    # Execute
    with manager.keep_cwd():
        if sandbox:
            imports = manager.modules()
            result = run_sandbox(
                run_from_lang,
                args=(manager.lang, manager.source, inputs),
                kwargs={'raises': raises, 'timeout': timeout},
                imports=imports,
            )
            result = IoSpec.from_json(result)
        else:
            result = run_from_manager(
                manager,
                inputs,
                raises=raises,
                timeout=timeout
            )
    return result


def grade(source, iospec, lang=None, *,
          fast=True, path=None, raises=False, sandbox=False, timeout=None):
    """
    Grade the string of source code by comparing the results of all inputs and
    outputs in the given template structure.


    Parameters
    ----------

    source : str or file object
        The source string for the code or a file object
    iospec : IOSpec parse tree
        The expected template for correct answers.
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
        |           | for debugging since it lack in features and performance  |
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

    Specific languages may support additional keyword arguments. The most common
    ones are shown bellow

    namespace (python): dict
        The global namespace used to run a python script.


    Returns
    -------

    A :cls:`ejudge.Feedback` instance.
    """

    manager = get_manager(lang, source, path)
    manager.is_sandboxed = sandbox

    # Normalize inputs
    if isinstance(iospec, str):
        iospec = parse_string(iospec)
    if not iospec:
        raise ValueError('cannot grade an iospec that has no cases')

    with manager.keep_cwd():
        kwargs = {'raises': raises, 'timeout': timeout, 'fast': fast}

        if sandbox:
            imports = manager.modules()
            result = run_sandbox(
                grade_from_lang,
                args=(manager.lang, manager.source, iospec.to_json()),
                kwargs=kwargs,
                imports=imports,
            )
            result = Feedback.from_json(result)
        else:
            # noinspection PyArgumentList
            result = grade_from_manager(manager, iospec, **kwargs)
    return result


def get_answer_key_error(source, iospec, lang, **kwargs):
    """Compares the results of running the given source code with the given
    iospec and return the first test case which fails.

    Return None if no test case fails and the answer key is acceptable."""


def grade_from_manager(manager, iospec, *, raises, timeout, fast):
    """Grade manager instance by comparing it to the given iospec."""

    try:
        manager.build()
        error_message = None
    except BuildError as ex:
        if raises:
            raise
        error_message = str(ex)

    value = decimal.Decimal(1)
    feedback = None

    for answer_key in iospec:
        # We run each test case and compare results. If there was a build error
        # and raises is False, we create a new ErrorTestCase for each time
        # the program is supposed to run.
        inputs = answer_key.inputs()
        if error_message:
            case = ErrorTestCase.build(error_message=error_message)
        else:
            try:
                case = manager.run(inputs, timeout=timeout)
            except Exception as ex:
                case = error_test_case(ex, ex.__traceback__)

        if not isinstance(case, TestCase):
            raise RuntimeError(
                'Manager %s .run() method did not return a TestCase: got a %s '
                'instance' % (type(manager).__name__, type(case).__name__),
            )

        # Compute feedback and compare with worst results
        curr_feedback = get_feedback(case, answer_key)

        if feedback is None:
            feedback = curr_feedback

        if curr_feedback.grade < value:
            feedback = curr_feedback
            value = curr_feedback.grade

            if value == 0 and fast:
                break

    return feedback


def grade_from_lang(lang, source, iospec, **kwargs):
    """A version of grade_from_manager() in which both the inputs and ouputs
    can be converted to JSON."""

    manager = manager_from_lang(lang, source)
    iospec = IoSpec.from_json(iospec)
    result = grade_from_manager(manager, iospec, **kwargs)
    return result.to_json()


def error_test_case(exc, tb, limit=None):
    """Return an IoSpec data with a single ErrorTestCase.

    Construct the testcase from the given traceback."""

    out = io.StringIO()
    traceback.print_tb(tb, file=out)
    _, sep, tail = out.getvalue().partition('  File "main.py", line')
    message = ('Traceback (most recent call last)\n%s%s: %s' %
               (sep + tail, exc.__class__.__name__, exc))
    return ErrorTestCase.runtime(error_message=message)


def run_from_manager(manager, inputs, *, raises, timeout):
    """Run command from given manager."""

    try:
        manager.build()
    except BuildError as ex:
        if raises:
            raise
        return IoSpec([ErrorTestCase.build(error_message=str(ex))])

    data = []
    for x in inputs:
        try:
            data.append(manager.run(x))
        except Exception as ex:
            if raises:
                raise
            data.append(error_test_case(ex, ex.__traceback__))
    result = IoSpec(data)
    result.setmeta('lang', manager.name)
    result.setmeta('buildargs', manager.buildargs)
    result.setmeta('shellargs', manager.shellargs)
    return result


def run_from_lang(lang, src, inputs, *, raises, timeout):
    """Calls run_from_manager, but uses only JSON-encodable arguments.

    This function should be used in sandboxed environments."""

    manager = manager_from_lang(lang, src)
    manager.is_sandboxed = True
    result = run_from_manager(manager, inputs, raises=raises, timeout=timeout)
    return result.to_json()


def get_manager(lang, src, path):
    """Return a manager instance from the given language, source and path."""

    # Fix language
    if lang is None:
        ext = os.path.splitext(path or src.name)[1] or '.'
        try:
            lang = lang_from_extension(ext)
        except KeyError:
            raise ValueError('unknown extension: %r' % ext)

    # Normalize source string
    if not isinstance(src, str):
        src = src.read()

    return manager_from_lang(lang, src)
