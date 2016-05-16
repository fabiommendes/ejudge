import io
import traceback
from iospec import types
from ejudge.langs import IntegratedLanguage, ScriptingLanguage


class Python3Mixin:
    def syntax_check(self):
        try:
            compile(self.source, 'main.py', 'exec')
        except SyntaxError:
            out = io.StringIO()
            traceback.print_exc(file=out, limit=0)
            msg = out.getvalue()
            raise SyntaxError(msg)

    def prepare_error(self, ex):
        """Formats exception"""

        exname = type(ex).__name__
        messages = []
        codelines = self.source.splitlines()
        tb = ex.__traceback__

        tblist = reversed(traceback.extract_tb(tb))
        for (filename, lineno, funcname, text) in tblist:
            if 'ejudge' in filename:
                break
            if filename == '<string>':
                text = codelines[lineno - 1].strip()
            messages.append((filename, lineno, funcname, text))

        messages.reverse()
        messages = traceback.format_list(messages)
        messages.insert(0, 'Traceback (most recent call last)')
        messages.append('%s: %s' % (exname, ex))
        return '\n'.join(messages)


class PythonManager(Python3Mixin, IntegratedLanguage):
    name = 'python'
    description = 'Python 3.x'
    extensions = ['py', 'py3']

    def exec(self, inputs, context):
        assert context is not None
        code = compile(self.source, 'main.py', 'exec')
        if hasattr(self.context, 'locals'):
            exec(code, context.globals, context.locals)
        else:
            exec(code, context.globals)
        return types.IoTestCase(self.flush_io())


class PythonScriptManager(Python3Mixin, ScriptingLanguage):
    name = 'python3'
    description = 'Python 3.x'
    extension = 'py'
    shellargs = ['python3', 'main.py']


class Python2Manager(ScriptingLanguage):
    name = 'python2'
    description = 'Python 2.7'
    extension = 'py'
    shellargs = ['python2', 'main.py']

    def syntax_check(self):
        pass

