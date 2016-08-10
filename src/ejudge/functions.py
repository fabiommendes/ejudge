import decimal
import io
import traceback

from boxed.jsonbox import run as run_sandbox
from ejudge import registry
from ejudge.exceptions import BuildError
from ejudge.util import keep_cwd
from iospec import parse_string, TestCase, ErrorTestCase, IoSpec
from iospec.feedback import feedback as get_feedback, Feedback


def run(source, inputs, lang=None, *,
        timeout=None, raises=False, path=None, sandbox=True):
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

    Returns:
        A :class:`iospec.IoSpec` structure. If ``inputs`` is a sequence of
        strings, the resulting tree will have a single test case.
    """

    build_manager = registry.build_manager_from_path(lang, source, path,
                                                     is_sandboxed=sandbox)

    # Normalize inputs
    if isinstance(inputs, (IoSpec, TestCase)):
        inputs = inputs.inputs()
    else:
        if isinstance(inputs[0], str):
            inputs = [list(inputs)]
        else:
            inputs = [list(x) for x in inputs]

    # Execute
    with keep_cwd():
        if sandbox:
            imports = build_manager.get_modules()
            result = run_sandbox(
                run_from_lang,
                args=(build_manager.language, build_manager.source, inputs),
                kwargs={'raises': raises, 'timeout': timeout},
                imports=imports,
            )
            result = IoSpec.from_json(result)
        else:
            result = run_from_manager(
                build_manager,
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

    build_manager = registry.build_manager_from_path(lang, source, path,
                                                     is_sandboxed=sandbox)

    # Normalize inputs
    if isinstance(iospec, str):
        iospec = parse_string(iospec)
    if not iospec:
        raise ValueError('cannot grade an iospec that has no cases')

    with keep_cwd():
        kwargs = {'raises': raises, 'timeout': timeout, 'fast': fast}

        if sandbox:
            imports = build_manager.get_modules()
            language = build_manager.language
            manager_source = build_manager.source
            result = run_sandbox(
                grade_from_lang,
                args=(language, manager_source, iospec.to_json()),
                kwargs=kwargs,
                imports=imports,
            )
            result = Feedback.from_json(result)
        else:
            result = grade_from_manager(build_manager, iospec, **kwargs)
    return result


def get_answer_key_error(source, iospec, lang, **kwargs):
    """
    Compares the results of running the given source code with the given
    iospec and return the first test case which fails.

    Return None if no test case fails and the answer key is acceptable.
    """


def grade_from_manager(build_manager, iospec, raises, timeout, fast):
    """
    Grade manager instance by comparing it to the given iospec.
    """

    try:
        build_manager.build()
        error_message = None
    except BuildError as ex:
        if raises:
            raise
        error_message = str(ex)

    value = decimal.Decimal(1)
    feedback = None
    language = build_manager.language

    for answer_key in iospec:
        # We run each test case and compare results. If there was a build error
        # and raises is False, we create a new ErrorTestCase for each time
        # the program is supposed to run.
        inputs = answer_key.inputs()
        if error_message:
            case = ErrorTestCase.build(error_message=error_message)
        else:
            ctrl = registry.execution_manager(language, build_manager,
                                              inputs)
            try:
                if timeout:
                    ctrl.run_with_timeout(timeout)
                else:
                    case = ctrl.run()
            except Exception as ex:
                case = error_test_case(ex, ex.__traceback__)

            if not isinstance(case, TestCase):
                raise RuntimeError(
                    '%s .run() method did not return a TestCase: got a %s '
                    'instance' % (type(ctrl).__name__,  type(case).__name__),
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
    """
    A version of grade_from_manager() in which both the inputs and outputs
    can be converted to JSON.
    """

    iospec = IoSpec.from_json(iospec)
    build_manager = registry.build_manager(lang, source)
    result = grade_from_manager(build_manager, iospec, **kwargs)
    return result.to_json()


def error_test_case(exc, tb, limit=None):
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


def run_from_manager(build_manager, input_sets, *, raises, timeout):
    """
    Run command from given ExecutionManager.
    """

    try:
        build_manager.build()
    except BuildError as ex:
        if raises:
            raise
        return IoSpec([ErrorTestCase.build(error_message=str(ex))])

    data = []
    for inputs in input_sets:
        language = build_manager.language
        ctrl = registry.execution_manager(language, build_manager, inputs)
        try:
            if timeout:
                result = ctrl.run()
            else:
                result = ctrl.run_with_timeout(timeout)
            data.append(result)
        except Exception as ex:
            if raises:
                raise
            data.append(error_test_case(ex, ex.__traceback__))
    result = IoSpec(data)
    result.set_meta('lang', build_manager.language)
    return result


def run_from_lang(lang, src, inputs, *, raises, timeout):
    """
    Calls run_from_manager, but uses only JSON-encodable arguments.

    This function should be used in sandboxed environments.
    """

    build_manager = registry.build_manager(lang, src, is_sandboxed=True)
    result = run_from_manager(
        build_manager, inputs, raises=raises, timeout=timeout
    )
    return result.to_json()
