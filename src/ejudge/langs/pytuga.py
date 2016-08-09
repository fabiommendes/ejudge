import pytuga
from ejudge.build_manager import IntegratedBuildManager
from ejudge.execution_manager import IntegratedExecutionManager


class PytugaBuildManager(IntegratedBuildManager):
    """
    Build manager for the Pytuga language.
    """

    def syntax_check(self):
        return NotImplemented

    def get_modules(self):
        return super().get_modules() + ['pytuga.lib.forbidden']


class PytugaExecutionManager(IntegratedExecutionManager):
    """
    Execution manager for the Pytugues language.
    """

    def exec(self, globals, locals):
        pytuga.exec(self.source, globals, locals, forbidden=True)
