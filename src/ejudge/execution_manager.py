import functools
import io
import multiprocessing
import os
import subprocess
import sys

from boxed.pinteract import Pinteract
from ejudge import builtins_ctrl
from ejudge.exceptions import MissingInputError
from ejudge.util import remove_trailing_newline_from_testcase, \
    timeout as run_with_timeout, format_traceback
from iospec import Out, In, datatypes, SimpleTestCase, ErrorTestCase


class ExecutionManager:
    """
    Controls execution of a single test case.

    Args:
        build_manager:
            The BuildManager instance associated with this program.
        inputs:
            A list of lists of input strings.
    """

    source = property(lambda self: self.build_manager.source)
    is_sandboxed = property(lambda self: self.build_manager.is_sandboxed)

    def __init__(self, build_manager, inputs=()):
        self.build_manager = build_manager
        if inputs is None:
            self.inputs = None
        else:
            self.inputs = tuple(inputs)
        self.is_started = False
        self.is_closed = False

    def add_input(self, input_str):
        """
        Add an input string to the end of registered inputs.
        """

        self.inputs += (input_str,)

    def add_inputs(self, seq):
        """
        Add a sequence of input strings to the end of registered inputs.
        """

        self.inputs += tuple(seq)

    def run(self):
        """
        Run program and return a list of In/Out elements interactions.
        """

        if self.is_closed or self.build_manager.is_closed:
            raise RuntimeError(
                'Program already executed. Cannot run it again.'
            )
        if self.is_started:
            raise RuntimeError(
                'Program already started execution. Please create another '
                'ExecutionManager instance.'
            )
        self.start()
        result = self.interact()
        self.end()
        return remove_trailing_newline_from_testcase(result)

    def run_interactive(self):
        """
        Run program asking user for input.
        """

        if self.is_closed or self.build_manager.is_closed:
            raise RuntimeError(
                'Program already executed. Cannot run it again.'
            )
        if self.is_started:
            raise RuntimeError(
                'Program already started execution. Please create another '
                'ExecutionManager instance.'
            )
        self.start()
        self.interact_with_user()
        self.end()

    def run_with_timeout(self, timeout):
        """
        Run execution with a given timeout.
        """

        return run_with_timeout(self.run, timeout=timeout)

    def interact(self):
        """
        Interact with the program by using all input strings.

        Return a IoSpec.TestCase instance with the results of interaction.
        """

        raise NotImplementedError

    def interact_with_user(self):
        """
        Starts and executes program without storing any inputs.
        """

        raise NotImplementedError

    def start(self):
        """
        Executed to start program execution.
        """

        if not self.build_manager.is_built:
            self.build_manager.build()
        self.is_started = True

    def end(self):
        """
        Executed after execution ends. May be necessary to clean state.
        """

        self.is_closed = True


class IntegratedExecutionManager(ExecutionManager):
    """
    Execution manager for Python or other languages integrated into the Python
    interpreter.
    """
    __print = staticmethod(print)
    __input = staticmethod(input)

    def __init__(self, build_manager, inputs):
        super().__init__(build_manager, inputs)
        self.interaction = []
        self.is_isolated = False

    def interact_integrated(self):
        builtins_ctrl.update(self.builtins())
        try:
            if self.build_manager.locals is None:
                locals_dic = None
            else:
                locals_dic = dict(self.build_manager.locals)
            globals_dic = dict(self.build_manager.globals or {})
            try:
                self.exec(globals_dic, locals_dic)
                result = SimpleTestCase(self.interaction)
            except Exception as ex:
                error = format_traceback(ex, self.source)
                result = ErrorTestCase.runtime(
                    self.interaction,
                    error_message=error,
                )
        finally:
            builtins_ctrl.restore()

        return result

    def interact_with_user(self):
        if self.build_manager.locals is None:
            locals_dic = None
        else:
            locals_dic = dict(self.build_manager.locals)
        globals_dic = dict(self.build_manager.globals or {})
        self.exec(globals_dic, locals_dic)

    def interact(self):
        if self.is_sandboxed:
            return self.interact_integrated()
        else:
            # We spawn and immediately join the child process in order to
            # execute the integrated manager in a separate environment. This
            # isolation is important in execution environments that introduce
            # global state to the interpreter.
            #
            # Since python do not really prevent scripts from introducing global
            # state, we always isolate execution this way to prevent any
            # potentially dangerous global state to leak into the main
            # interpreter process.
            queue = multiprocessing.Queue()
            process = multiprocessing.Process(
                target=integrated_manager_interact,
                kwargs={
                    'queue': queue,
                    'inputs': self.inputs,
                    'build_manager': self.build_manager,
                    'execution_manager_class': type(self),
                }
            )
            process.start()
            process.join()
            return queue.get()

    # noinspection PyShadowingBuiltins
    def exec(self, globals, locals):
        """
        Execute code with the given locals and globals.
        """

        code = compile(self.source, 'main.py', 'exec')

        if locals is None:
            exec(code, globals)
        else:
            exec(code, globals, locals)

    def builtins(self):
        """
        Return a dictionary with builtin functions replacements.

        The default implementation just replaces the builtin print() and input()
        functions.
        """
        consumed_inputs = list(self.inputs)[::-1]

        @functools.wraps(self.__print)
        def print(*args, sep=' ', end='\n', file=None, flush=False):
            if not (file is None or file is sys.stdout):
                self.__print(*args, sep=sep, end=end, file=file, flush=flush)
            else:
                file = io.StringIO()
                self.__print(*args, sep=sep, end=end, file=file, flush=flush)
                data = file.getvalue()

                if self.interaction and isinstance(self.interaction[-1], Out):
                    self.interaction[-1] += Out(data)
                else:
                    self.interaction.append(Out(data))

        @functools.wraps(self.__input)
        def input(prompt=None):
            if prompt is not None:
                print(prompt, end='')
            if consumed_inputs:
                result = consumed_inputs.pop()
                self.interaction.append(In(result))
                return result
            else:
                raise MissingInputError('not enough inputs')

        return {'print': print, 'input': input}


class PInteractExecutionManager(ExecutionManager):
    """
    Execution manager for languages executed outside the main Python 3
    interpreter.
    """

    shell_args = None

    def interact(self):
        return self.run_pinteract(self.get_shell_args())

    def interact_with_user(self):
        os.chdir(self.build_manager.build_path)
        try:
            shell_args = self.get_shell_args()
            subprocess.check_call(shell_args)
        except subprocess.CalledProcessError as ex:
            raise RuntimeError('%r executed with error: %s' % (shell_args, ex))

    def run_pinteract(self, shell_args):
        """
        Run script as a subprocess and gather results of execution.

        This is a generic implementation. Specific languages or runtimes are
        supported by fixing the shellargs argument of this function.
        This function uses the PInteract() object for communication with
        scripts.

        This function may change the current working path.
        """

        def append_non_empty_output():
            data = process.receive()
            if data:
                result.append(datatypes.Out(data))

        # Execute script in the tempdir and than go back once execution has
        # finished
        result = SimpleTestCase()
        current_dir = os.getcwd()

        try:
            os.chdir(self.build_manager.build_path)
            process = Pinteract(shell_args)

            # Fetch all In/Out strings
            append_non_empty_output()
            for idx, inpt in enumerate(self.inputs):
                try:
                    process.send(inpt)
                    result.append(datatypes.In(inpt))
                except RuntimeError as ex:
                    # Early termination: we still have to decide if an specific
                    # early termination error should exist.
                    #
                    # The default behavior is just to send a truncated
                    # IoTestCase
                    if process.is_dead():
                        missing = self.inputs[idx:]
                        missing_str = '\n'.join('    ' + x for x in missing)
                        msg = ('process closed with consuming all inputs. '
                               'List of unused inputs:\n')

                        return ErrorTestCase.runtime(
                            list(result),
                            error_message=msg + '\n' + missing_str
                        )

                    # This clause is just a safeguard. We don't expect to ever
                    # get here
                    return ErrorTestCase.runtime(
                        list(result),
                        error_message='An internal error occurred while trying '
                                      'to interact with the script: %s.' % ex
                    )
                append_non_empty_output()
        finally:
            if not self.is_sandboxed:
                os.chdir(current_dir)

        # Finish process
        error_ = process.finish()
        assert not any(error_), error_
        return result

    def get_shell_args(self):
        """
        Return the arguments passed to the executable object.
        """

        if self.shell_args is None:
            raise NotImplementedError(
                'Subclasses must either define the .shell_args attribute or '
                'override the .get_shell_args() method.'
            )
        if isinstance(self.shell_args, str):
            import shlex
            return shlex.split(self.shell_args)
        return list(self.shell_args)


class CompiledLanguageExecutionManager(PInteractExecutionManager):
    """
    Base execution manager for compiled languages.

    It assumes that the compiled executable is named "main.exe" and is inside
    the build directory.
    """

    shell_args = ['./main.exe']


class InterpretedLanguageExecutionManager(PInteractExecutionManager):
    """
    Base execution manager for interpreted languages.

    It assumes the main interpreter will just execute the source file.
    """

    interpreter_command = None

    def get_interpreter_command(self):
        """
        Return the command to execute the interpreter.
        """

        if self.interpreter_command is None:
            raise NotImplementedError(
                'Subclasses must either supply the .interpreter_command '
                'string attribute or override the get_interpreter_command() '
                'method.'
            )

        source_name = self.build_manager.get_source_filename()
        return [self.interpreter_command, source_name]

    def get_shell_args(self):
        if self.shell_args is None:
            return self.get_interpreter_command()
        else:
            return self.shell_args


# Interact with integrated manager as the target function in a subprocess
# execution.
def integrated_manager_interact(queue, inputs, build_manager,
                                execution_manager_class):
    exc_manager = execution_manager_class(build_manager, inputs)
    result = exc_manager.interact_integrated()
    queue.put(result)
