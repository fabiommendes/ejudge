import io
import os
import stat
import abc
import sys
import tempfile
import contextlib
import subprocess
import importlib
import traceback
from boxed.pinteract import Pinteract
from iospec.types import AttrDict
from iospec import types
from iospec.runners import IoObserver
from iospec.util import indent
from ejudge import builtin_mgm
from ejudge import util
from ejudge.util import real_print

__all__ = ['IntegratedLanguage', 'ScriptingLanguage', 'CompiledLanguage',
           'BuildError', 'manager_from_lang', 'lang_from_extension']
_print = print
_stdout = sys.stdout
lang_mapping = {
}


class BuildError(Exception):
    pass


class LanguageManager:
    """
    Support for new languages is done by subclassing this class.

    The LanguageManager automatically register new classes using meta
    information that is passed as class attributes. It requires that the
    following attributes are defined:

    name : str
        Short lowercase name for the language. (e.g.: python)
    description : str
        A short description of the language (appending version numbers and
        possibly compile flags). (e.g.: Python 3.x)
    extensions:
        A list of valid extensions associated to that language.
    """

    abstract = True
    supported_languages = {}
    registered_extensions = {}
    registered_language_extensions = {}
    buildargs = None
    shellargs = None
    _send_early_termination_error = False

    @property
    def lang(self):
        return self.name

    def __init__(self, source, is_sandboxed=True):
        self.source = source
        self.context = None
        self.is_sandboxed = is_sandboxed

    @classmethod
    def from_language(cls, lang, source):
        try:
            factory = cls.supported_languages[lang]
        except KeyError:
            raise ValueError('invalid language: %r' % lang)
        return factory(source)

    @abc.abstractmethod
    def build_context(self):
        """Returns the build context for the given manager.

        This function is only called if self.syntax_check() has passed.

        Failed builds can either return None or raise a BuildError."""

        raise NotImplementedError

    @abc.abstractmethod
    def exec(self, inputs, context):
        """Executes the source code in the given context and return the
        resulting test case object

        The context parameter is the result of calling the build function."""

        raise NotImplementedError

    @abc.abstractmethod
    def syntax_check(self):
        raise SyntaxError('invalid syntax')

    def build(self):
        """Builds and check the source code syntax. Also prepares the
        environment before execution.

        This function can be called multiple times and it will return a cached
        build context."""

        if self.context is None:
            try:
                self.syntax_check()
            except SyntaxError as ex:
                file = io.StringIO()
                traceback.print_tb(ex.__traceback__, file=file)
                message = '%s%s: %s' % (file.getvalue(),
                                        ex.__class__.__name__, ex)
                raise BuildError(ex)

            self.context = self.build_context()
            if self.context is None:
                data = indent(self.source)
                raise BuildError('cannot build source: \n%s' % data)
        return self.context

    def reset_context(self):
        """Reset/reconfigure the self.context attribute after each run.

        The default implementation does nothing."""

    def prepare_error(self, ex):
        """Prepares an exception receiving trying to execute
        manager.exec(ctx, inputs) before it is inserted into the error attribute
        of the returning ErrorTestCase."""

        return str(ex)

    def flush_io(self):
        """Flush all io buffers and return what has been collected so far.

        The resulting value is a list of plain input or output nodes."""

        return []

    def run(self, inputs, *, timeout=None, context=None):
        """Executes the program with the given inputs"""

        inputs = map(str, inputs)
        if context is None:
            context = self.build()

        try:
            func = self.exec
            result = remove_trailing_newline(
                    util.timeout(func, args=(inputs, context), timeout=timeout))

        except TimeoutError as ex:
            msg = 'Maximum execution time exceeded: %s sec' % timeout
            result = types.ErrorTestCase.timeout(
                data=self.flush_io(),
                error_message=msg)

        # Reset context before returning
        self.reset_context()
        return result

    def modules(self):
        """Return a list of module imports that should be passed to the
        boxed.run() function in sandboxed mode."""

        return [self.__module__]

    @contextlib.contextmanager
    def keep_cwd(self):
        """A utility function that implements a context manager that restores
        the cwd at the beginning of execution when it exits the with block."""

        currpath = os.getcwd()
        yield
        os.chdir(currpath)


# noinspection PyAbstractClass
class IntegratedLanguage(LanguageManager):
    """Base class for all languages that expose hooks for printing and input
    directly to Python's interpreter itself.

    This runner is the most integrated with the ejudge system. Ideally all
    languages should be implemented as subclasses of IntegratedLanguage.
    This may not be feasible or practical for most programming languages,
    though."""

    abstract = True

    def __init__(self, source, globals=None, locals=None, builtins=None):
        super().__init__(source)
        self.observer = IoObserver()
        self.globals = dict(globals or {})
        self.locals = None if locals is None else dict(locals)
        self.builtins = {
            'print': self.observer.print,
            'input': self.observer.input,
        }
        self.builtins.update(builtins or {})

    def build_context(self):
        globs = self.globals.copy()
        if self.locals is None:
            return AttrDict(globals=globs)
        else:
            return AttrDict(globals=globs, locals=self.locals.copy())

    def reset_context(self):
        self.context.globals = self.globals.copy()
        if 'locals' in self.context:
            self.context.locals = self.locals.copy()

    def flush_io(self):
        return self.observer.flush()

    def run(self, inputs, **kwds):
        builtin_mgm.update(self.builtins)
        try:
            self.observer.flush()
            self.observer.extend_inputs(inputs)
            result = super().run(inputs, **kwds)
        finally:
            builtin_mgm.restore()

        return remove_trailing_newline(result)

    def syntax_check(self):
        raise NotImplementedError('no syntax check implemented for %s' %
                                  type(self).__name__)

    def print(self, *args, file=_stdout, **kwds):
        return _print(*args, file=file, **kwds)


class ExternalExecution(LanguageManager):
    """Features common to scripting and compiled languages or any language in
    which the runtime is outside the Python interpreter."""

    abstract = True

    @property
    def extension(self):
        return self.extensions[0]

    @property
    def shellargs(self):
        raise RuntimeError('shellargs must be overriden in the subclass')

    def exec(self, inputs, context):
        return self.exec_pinteract(inputs, context)

    def exec_pinteract(self, inputs, context):
        """Run script as a subprocess and gather results of execution.

        This is a generic implementation. Specific languages or runtimes are
        supported by fixing the shellargs argument of this function.
        This function uses the PInteract() object for communication with
        scripts.

        This function may change the current working path.
        """

        def append_non_empty_out():
            data = process.receive()
            if data:
                result.append(types.Out(data))

        tmpdir = context.tempdir
        result = types.IoTestCase()

        # Execute script in the tmpdir and than go back once execution has
        # finished
        olddir = os.getcwd()
        os.chdir(tmpdir)

        try:
            process = Pinteract(self.shellargs)

            # Fetch all In/Out strings
            append_non_empty_out()
            for inpt in inputs:
                try:
                    process.send(inpt)
                    result.append(types.In(inpt))
                except RuntimeError as ex:
                    # Early termination: we still have to decide if an specific
                    # early termination error should exist.
                    #
                    # The default behavior is just to send a truncated
                    # IoTestCase
                    if process.is_dead():
                        if self._send_early_termination_error:
                            missing = [inpt]
                            missing.extend(inputs)
                            missing = '\n'.join('    ' + x for x in missing)
                            msg = ('process closed with consuming all inputs. '
                                   'List of unused inputs:\n')

                            return types.ErrorTestCase.earlytermination(
                                list(result),
                                error_message=msg + missing)
                        else:
                            return types.IoTestCase(list(result))

                    # This clause is just a safeguard. We don't expect to ever
                    # get here
                    return types.ErrorTestCase.runtime(
                        list(result),
                        error_message='An internal error occurred while trying '
                                      'to interact with the script: %s.' % ex
                    )
                append_non_empty_out()
        finally:
            if not self.is_sandboxed:
                os.chdir(olddir)

        # Finish process
        error_ = process.finish()
        assert not any(error_), error_
        return result


# noinspection PyAbstractClass
class ScriptingLanguage(ExternalExecution):
    """Basic support for scripting language."""

    abstract = True

    def build_context(self):
        """Base buildfunc for source code that can be executed as scripts.

        Concrete implementations must provide a default extension for the script
        files and a syntax_check(src) function, that takes a string of code and
        raise BuildProblem if the syntax is invalid."""

        tmpdir = tempfile.mkdtemp()
        tmppath = os.path.join(tmpdir, 'main.' + self.extension)

        # Make tmp directory readable and writable by everyone
        if self.is_sandboxed:
            os.chmod(tmpdir, stat.S_IEXEC | stat.S_IREAD | stat.S_IWRITE |
                             stat.S_IXOTH | stat.S_IROTH | stat.S_IWOTH |
                             stat.S_IXGRP | stat.S_IRGRP | stat.S_IWGRP)

        # Save source and make it readable by everyone
        with open(tmppath, 'w') as F:
            F.write(self.source)
        if self.is_sandboxed:
            os.chmod(tmppath, stat.S_IREAD | stat.S_IROTH | stat.S_IRGRP)

        return AttrDict(
            tempdir=tmpdir,
            shellargs=self.shellargs,
            messages='',
        )


class CompiledLanguage(ExternalExecution):
    abstract = True
    shellargs = ['./main.exe']

    def build_context(self):
        """Base build function for source code that must be compiled as part of the
        build process.

        Pass the list of shell arguments to run a command that takes a "main.ext"
        file and compiles it to "main.exe". Raises a BuildProblem if compilation
        return with a non-zero value."""

        # Save source file in temporary dir
        tmpdir = tempfile.mkdtemp()
        tmppath = os.path.join(tmpdir, 'main.' + self.extension)
        with open(tmppath, 'w') as F:
            F.write(self.source)

        # Compile and return
        currpath = os.getcwd()
        errmsgs = 'compilation is taking too long'
        try:
            os.chdir(tmpdir)
            buildargs = list(self.buildargs)
            errmsgs = subprocess.check_output(self.buildargs, timeout=10)

            # Make executable readable and executable by everyone
            if self.is_sandboxed:
                os.chmod('main.exe',
                         stat.S_IREAD | stat.S_IROTH | stat.S_IRGRP |
                         stat.S_IEXEC | stat.S_IXOTH | stat.S_IXGRP)

        except (subprocess.CalledProcessError, TimeoutError):
            raise BuildError(errmsgs)
        finally:
            # Cannot return to path in sandboxed mode since the nobody user
            # probably does not have read permissions on the old working
            # directory
            if not self.is_sandboxed:
                os.chdir(currpath)

        return AttrDict(tempdir=tmpdir, shellargs=self.shellargs,
                        messages=errmsgs)


def remove_trailing_newline(case):
    """Remove a trailing newline from the last output node."""

    if case is None:
        return None

    if case:
        last = case[-1]
        if isinstance(last, types.Out) and last.endswith('\n'):
            last.data = str(last[:-1])
    return case


#
# API function
#
ext_map = {}
lang_map = {}


def manager_from_lang(lang, src, **kwds):
    """Return a manager instance for the given language string.

    It passes the code source and any other keyword arguments that might be
    necessary to the correct initialization of the manager."""

    manager = lang_map[lang]

    if isinstance(manager, str):
        mod_name, _, manager_name = manager.rpartition('.')
        mod = importlib.import_module(mod_name)
        manager = getattr(mod, manager_name)

    return manager(src, **kwds)


def lang_from_extension(ext):
    """Return a lang string from the given extension."""

    if ext.startswith('.'):
        ext = ext[1:]
    return ext_map[ext]


def register_extension(ext, lang, force=False):
    """Map an extension to a given lang."""

    if ext.startswith('.'):
        ext = ext[1:]
    if force and ext in ext_map and ext != ext_map[lang]:
        raise RuntimeError('extension %r is already registered to %r' %
                           ('.' + ext, lang))
    ext_map[ext] = lang


def register_lang(lang, cls=None, force=False, extensions=(), aliases=()):
    """Register a LanguageManager class `cls` tho the given language `lang`.

    This function accepts either the class itself or a named reference such
    as "ejudge.langs.lang_c.GccManager".

    If force=True, it overwrites any manager class already registered to a
    language."""

    if cls is None:
        def decorator(cls):
            register_lang(lang, cls, force=force)
            return cls

    if force and lang in lang_map and lang_map[lang] != cls:
        raise RuntimeError('%r is already registered to %r' % (lang, cls))

    for ext in extensions:
        register_extension(ext, lang, force=force)

    lang_map[lang] = cls
    for alias in aliases:
        lang_map[alias] = cls


#
# Explicitly register supported languages
#

# C family languages
register_lang('c', 'ejudge.langs.lang_c.GccManager',
              extensions=['.c'], aliases=['gcc'])
register_lang('tcc', 'ejudge.langs.lang_c.TccManager')
register_lang('clang', 'ejudge.langs.lang_c.ClangManager')
register_lang('c++', 'ejudge.langs.lang_c.GccCppManager',
              extensions=['.cpp'], aliases=['cpp', 'g++', 'gpp'])
register_lang('clang-c++', 'ejudge.langs.lang_c.ClangCppManager',
              aliases=['clang-cpp', 'clang++', 'clangpp'])

# Python family
register_lang('python', 'ejudge.langs.lang_python.PythonManager',
              extensions=['.py', 'py3'], aliases=['python3', 'py3', 'py'])
register_lang('python2', 'ejudge.langs.lang_python.Python2Manager',
              extensions=['.py2'], aliases=['python2', 'py2'])
register_lang('python-script', 'ejudge.langs.lang_python.PythonScriptManager')


# Exotic and special purpose languages
register_lang('pytuga', 'ejudge.langs.lang_pytuga.PytugaManager',
              extensions=['.pytg'], aliases=['pytg', 'pytugues', 'pytuguês'])