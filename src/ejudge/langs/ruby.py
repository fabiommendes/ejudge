from ejudge.build_manager import InterpretedLanguageBuildManager
from ejudge.execution_manager import InterpretedLanguageExecutionManager


class RubyBuildManager(InterpretedLanguageBuildManager):
    """
    Ruby builder.
    """

    source_extension = '.rb'

    def syntax_check(self):
        """
        Checks code for syntax errors.
        """

        #TODO: implement ruby syntax check.


class RubyExecutionManager(InterpretedLanguageExecutionManager):
    """
    Executes Ruby code.
    """

    interpreter_command = 'ruby'
