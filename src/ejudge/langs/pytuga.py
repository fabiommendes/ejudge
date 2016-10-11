import builtins
import pytuga
from ejudge.build_manager import IntegratedBuildManager
from ejudge.execution_manager import IntegratedExecutionManager


class PytugaBuildManager(IntegratedBuildManager):
    """
    Build manager for the Pytuga language.
    """

    language = 'pytuga'
    transpiled = ''

    def syntax_check(self):
        pytuga.compile(self.source, 'main.pytg', 'exec')

    def build(self):
        super().build()
        self.is_built = False
        self.transpiled = pytuga.transpile(self.source)
        self.is_built = True

    def get_modules(self):
        return super().get_modules() + ['pytuga.lib.forbidden']


class PytugaExecutionManager(IntegratedExecutionManager):
    """
    Execution manager for the Pytugues language.
    """

    language = 'pytuga'

    @property
    def transpiled(self):
        return self.build_manager.transpiled

    def exec(self, globals, locals):
        if globals is None:
            globals = {}
        globals.update(pytuga.tugalib_namespace(forbidden=True))
        builtins.exec(self.transpiled, globals, locals)