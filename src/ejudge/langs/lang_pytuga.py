import pytuga
from iospec import types
from ejudge.langs import ScriptingLanguage, IntegratedLanguage


class PytugaManager(IntegratedLanguage, ScriptingLanguage):
    # abstract = True
    name = 'pytuga'
    description = 'Pytuguês'
    extensions = ['pytg']
    shellargs = ['pytuga', 'main.pytg']

    def syntax_check(self):
        return NotImplemented

    @property
    def _base(self):
        return IntegratedLanguage if self.is_sandboxed else ScriptingLanguage

    def build_context(self):
        return self._base.build_context(self)

    def exec_integrated(self, inputs, context):
        assert context is not None
        pytuga.exec(self.source, context.globals, context.locals,
                    forbidden=True)
        return types.IoTestCase(self.flush_io())

    def exec(self, inputs, context):
        if self.is_sandboxed:
            return self.exec_integrated(inputs, context)
        else:
            return ScriptingLanguage.exec(self, inputs, context)

    def run(self, inputs, **kwds):
        return self._base.run(self, inputs, **kwds)

    def modules(self):
        return super().modules() + ['pytuga.lib.forbidden']
