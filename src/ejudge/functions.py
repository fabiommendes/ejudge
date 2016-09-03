import decimal
import io
import traceback

from boxed.jsonbox import run as run_sandbox
from ejudge import registry
from ejudge.exceptions import BuildError
from ejudge.util import keep_cwd, do_nothing_context_manager
from iospec import parse_string, TestCase, ErrorTestCase, IoSpec
from iospec.feedback import feedback as get_feedback, Feedback


def run(source, inputs, lang=None, *,
        fast=False, timeout=None, raises=False, path=None, sandbox=True,
        **kwargs):
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
    Returns:
        A :class:`iospec.IoSpec` structure. If ``inputs`` is a sequence of
        strings, the resulting tree will have a single test case.
    """

    # Normalize inputs
    if isinstance(inputs, (IoSpec, TestCase)):
        inputs = inputs.inputs()
    else:
        if isinstance(inputs[0], str):
            inputs = [list(inputs)]
        else:
            inputs = [list(x) for x in inputs]

    # Optional arguments
    is_sandboxed = kwargs.get('_is_sandboxed', False)
    return_json = kwargs.get('_return_json', False)

    # Create build manager
    build_manager = registry.build_manager_from_path(
        lang, source, path,
        is_sandboxed=is_sandboxed
    )

    # Run in sandboxed mode
    if sandbox:
        imports = build_manager.get_modules()
        result = run_sandbox(
            run,
            args=(source, inputs, lang),
            kwargs={
                'raises': raises,
                'timeout': timeout,
                'fast': fast,
                'path': path,
                'sandbox': False,
                '_is_sandboxed': True,
                '_return_json': True
            },
            imports=imports,
        )
        return IoSpec.from_json(result)

    # If running inside a sandbox, we must not try to restore the cwd
    if is_sandboxed:
        ctx_manager = do_nothing_context_manager()
    else:
        ctx_manager = keep_cwd()

    with ctx_manager:
        # Prepare build manager
        try:
            build_manager.build()
        except BuildError as ex:
            if raises:
                raise
            result = IoSpec([ErrorTestCase.build(error_message=str(ex))])
            return result.to_json() if return_json else result

        # Run all examples with the execution manager
        data = []
        language = build_manager.language
        for input_strings in inputs:
            ctrl = registry.execution_manager(language, build_manager,
                                              input_strings)
            try:
                if timeout:
                    result = ctrl.run()
                else:
                    result = ctrl.run_with_timeout(timeout)
            except Exception as ex:
                if raises:
                    raise
                result = _error_test_case(ex, ex.__traceback__)
            data.append(result)
            if fast and result.is_error:
                break

        # Prepare resulting iospec object
        result = IoSpec(data)
        result.set_meta('lang', build_manager.language)
        if return_json:
            return result.to_json()
        else:
            return result


def grade(source, iospec, lang=None, *,
          fast=True, path=None, raises=False, sandbox=False, timeout=None):
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
        iospec = parse_string(iospec)
    result = run(source, iospec, lang, fast=fast, path=path, raises=raises, sandbox=sandbox, timeout=timeout)
    feedback = None
    value = decimal.Decimal(1)

    for case, answer_key in zip(result, iospec):
        curr_feedback = get_feedback(case, answer_key)
        if feedback is None:
            feedback = curr_feedback
        if curr_feedback.grade < value:
            feedback = curr_feedback
            value = curr_feedback.grade
            if value == 0 and fast:
                break
    return feedback


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

