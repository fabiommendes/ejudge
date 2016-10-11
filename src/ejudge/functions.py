import io
import logging
import traceback

import sys

from boxed.core import capture_print
from boxed.jsonbox import run as run_sandbox
from ejudge import registry
from ejudge.exceptions import BuildError
from iospec import parse as ioparse, TestCase, ErrorTestCase, IoSpec
from iospec.feedback import feedback as get_feedback

logger = logging.getLogger('ejudge')


def run(source, inputs, lang=None, *,
        fast=False, timeout=None, raises=False, path=None, sandbox=True,
        compare_streams=False, fake_sandbox=False, debug=False):
    """
    Run program with the given list of inputs and returns the corresponding
    :class:`iospec.IoSpec` instance with the results.

    Args:
        source (str or file)
            The source code for the test program
        inputs (sequence)
            A sequence of input strings. If input is a sequence of sequences,
            this function will perform multiple test cases. It can also be a
            IoSpec or a TestCase instance which are used to extract the
            necessary input strings.
        lang (str)
            The name for the source code language. See
            :func:`ejudge.graders.io.grade` for more details.
        timeout (float)
            A time limit for the entire run (in seconds). If this attribute is
            not given, the program will run without any timeout. This can be
            potentially dangerous if the input program has an infinite loop.
        sandbox (bool)
            Controls if code is run in sandboxed mode or not. Sandbox protection
            is the default behavior on supported platforms.
        raises (bool)
            If True, raise a BuildError if the build process fails. The default
            behavior is to return a IoSpec instance with a single ErrorTestCase
            with a type string of 'error-build'.
        path (str)
            The absolute file path for the input string or file object.
        fast (bool):
            If true, stops running at the first error.
        compare_streams:
            If True, collect only the raw stdin and stdout streams. The default
            behavior is trying to collect fine-grained interactions.
    Returns:
        A :class:`iospec.IoSpec` structure. If ``inputs`` is a sequence of
        strings, the resulting tree will have a single test case.
    """

    return run_worker(**locals())[0]


def run_worker(source, inputs, lang=None, *,
               fast=False, timeout=None, raises=False, path=None, sandbox=True,
               compare_streams=False, is_sandboxed=False, fake_sandbox=False,
               debug=False):
    # Normalize inputs
    if isinstance(inputs, (IoSpec, TestCase)):
        inputs = inputs.inputs()
    else:
        if inputs and isinstance(inputs[0], str):
            inputs = [list(inputs)]
        else:
            inputs = [list(map(str, x)) for x in inputs]

    # Validate params
    if timeout is not None and timeout <= 0:
        raise ValueError('timeout must be positive, got: %s' % timeout)
    if sandbox and is_sandboxed:
        raise ValueError('cannot set sandbox = is_sandboxed = True')

    # Create build manager
    build_manager = registry.build_manager_from_path(
        lang, source, path,
        is_sandboxed=is_sandboxed,
        compare_streams=compare_streams,
    )

    # Run in sandboxed mode
    if sandbox:
        logger.debug('executing %s program inside sandbox' % lang)
        imports = build_manager.get_modules()
        args = (source, inputs, lang)
        kwargs = {
            'raises': raises,
            'timeout': timeout,
            'fast': fast,
            'path': path,
            'sandbox': False,
            'compare_streams': compare_streams,
            'is_sandboxed': True,
        }

        if fake_sandbox:
            result, messages = run_worker(*args, **kwargs)
        else:
            try:
                with capture_print() as data:
                    result, messages = run_sandbox(
                        run_worker,
                        args=args,
                        kwargs=kwargs,
                        imports=imports,
                        print_messages=True,
                    )
            except Exception:
                print(data.read(), file=sys.stderr)
                raise

        for (level, message) in messages:
            getattr(logger, level)(message)

        return IoSpec.from_json(result), []

    # Prepare build manager
    try:
        build_manager.build()
    except BuildError as ex:
        if raises:
            raise
        result = IoSpec([ErrorTestCase.build(error_message=str(ex))])
        if is_sandboxed:
            return result.to_json(), []
        else:
            return result, []

    # Run all examples with the execution manager
    data = []
    language = build_manager.language
    for input_strings in inputs:
        ctrl = registry.execution_manager(language, build_manager,
                                          input_strings)
        result = ctrl.run(timeout)
        assert isinstance(result, TestCase)
        data.append(result)
        if fast and result.is_error:
            break

    build_manager.log('info', 'executed all %s testcases in %s sec' %
                      (len(inputs), build_manager.execution_duration))

    # Prepare resulting iospec object
    result = IoSpec(data)
    result.set_meta('lang', build_manager.language)
    if is_sandboxed:
        return result.to_json(), build_manager.messages
    else:
        return result, []


def grade(source, iospec, lang=None, *,
          fast=True, path=None, raises=False, sandbox=False, timeout=None,
          compare_streams=False):
    """
    Grade the string of source code by comparing the results of all inputs and
    outputs in the given template structure.


    Args:
        source (str or file object)
            The source string for the code or a file object
        iospec (IOSpec parse tree)
            The expected template for correct answers.
        lang (str)
            Programming language for the given source code. Users can implement
            plugins to support additional languages or to override the default
            behavior or accepted languages.

            +-----------+------------------------------------------------------+
            | Value     | Description                                          |
            +===========+======================================================+
            | python    | For Python 3.x code. Default runner.                 |
            +-----------+------------------------------------------------------+
            | python2   | Executes in a separate Python 2 interpreter.         |
            +-----------+------------------------------------------------------+
            | tcc       | Compile C code with the tiny C compiler              |
            +-----------+------------------------------------------------------+
            | clang     | Compile C code with clang                            |
            +-----------+------------------------------------------------------+
            | gcc, c    | Compile C code with gcc                              |
            +-----------+------------------------------------------------------+

        sandbox (bool)
            If True, code will run in a sandboxed environment as the `nobody`
            user. It is necessary to have your system properly configured in
            order to do this.
        timeout (float)
            Maximum time (in seconds) for the complete test to run.

    Returns:
        A :class:`ejudge.Feedback` instance.
    """

    if isinstance(iospec, str):
        iospec = ioparse(iospec)
    kwargs = locals()
    kwargs['inputs'] = kwargs.pop('iospec')
    result = run(**kwargs)
    return get_feedback(result, iospec, stream=compare_streams)


def exec(source, lang=None, path=None):
    """
    Execute code in the given language.

    Do not pass any inputs or collect the outputs.
    """

    # Create build manager
    build_manager = registry.build_manager_from_path(
        lang, source, path,
        is_sandboxed=False,
    )
    build_manager.build()
    ctrl = registry.execution_manager(lang, build_manager)
    ctrl.run_interactive()


def _error_test_case(exc, tb, limit=None):
    """
    Return an IoSpec data with a single ErrorTestCase.

    Construct the testcase from the given traceback.
    """

    out = io.StringIO()
    traceback.print_tb(tb, file=out)
    _, sep, tail = out.getvalue().partition('  File "main.py", line')
    message = ('Traceback (most recent call last)\n%s%s: %s' %
               (sep + tail, exc.__class__.__name__, exc))
    return ErrorTestCase.runtime(error_message=message)
