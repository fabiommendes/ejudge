import subprocess
import tempfile

from ejudge.build_manager import IntegratedBuildManager, \
    InterpretedLanguageBuildManager
from ejudge.execution_manager import IntegratedExecutionManager, \
    InterpretedLanguageExecutionManager
from ejudge.util import format_traceback


# Python 3.x support
class PythonBuildManager(IntegratedBuildManager):
    """
    Integrated build manager for Python 3.x.
    """

    language = 'python'

    def syntax_check(self):
        python3_syntax_check(self.source)


class PythonExecutionManager(IntegratedExecutionManager):
    """
    Execution manager for Python source.
    """


# Python 3.x support in an isolated interpreter. This is implemented only for
# debug purposes
class PythonScriptBuildManager(InterpretedLanguageBuildManager):
    """
    Python 3.x builder that executes code in a separate interpreter.
    """

    source_extension = '.py'
    language = 'python-script'

    def syntax_check(self):
        python3_syntax_check(self.source)


class PythonScriptExecutionManager(InterpretedLanguageExecutionManager):
    """
    Python 3.x execution in a separate interpreter.
    """

    interpreter_command = 'python3'


# Python 2.7 support
class Python2BuildManager(InterpretedLanguageBuildManager):
    """
    Builds Python 2.7 code.
    """

    source_extension = '.py'
    language = 'python2'

    def syntax_check(self):
        with tempfile.NamedTemporaryFile(mode='w',
                                         suffix='.py',
                                         encoding='utf8',
                                         delete=False) as F:
            F.write(self.source)
            filename = F.name

        check = "f = '%s';compile(open(f).read(), f, 'exec')" % filename
        try:
            subprocess.check_output(['python2', '-s', '-S', '-E', '-c', check],
                                    stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as ex:
            data = ex.output
            data = data.decode('utf8')
            raise SyntaxError(data)


class Python2ExecutionManager(InterpretedLanguageExecutionManager):
    """
    Executes Python 2.7 code.
    """

    interpreter_command = 'python2'

    def get_interpreter_command(self):
        source_name = self.build_manager.get_source_filename()
        return ['python2', '-E', '-s', '-S', source_name]


# Utility functions
def python3_syntax_check(source):
    """
    Checks if string of source code is valid Python 3 syntax.
    """

    try:
        compile(source, 'main.py', 'exec')
    except SyntaxError as ex:
        msg = format_traceback(ex, source)
        raise SyntaxError(msg)
