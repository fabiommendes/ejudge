import logging
import os
import stat
import subprocess
import tempfile
import time

from ejudge.exceptions import BuildError

logger = logging.getLogger('ejudge')


class BuildManager:
    """
    Stores information about a program build.
    """

    @classmethod
    def from_json(cls, json):
        return cls(**json)

    def __init__(self, source, is_sandboxed=False, modules=None,
                 compare_streams=None):
        self.source = source
        self.modules = modules
        self.is_sandboxed = is_sandboxed
        self.compare_streams = compare_streams
        self.is_built = False
        self.is_closed = False
        self.messages = []
        self.has_successful_execution = False
        self.build_duration = 0
        self.execution_duration = 0
        self.start_time = time.time()

    def log(self, level, message):
        """
        Log message for the given log level.
        """

        if self.is_sandboxed:
            self.messages.append((level, message))
        else:
            getattr(logger, level)(message)

    def build(self, _log=True):
        """
        Prepares build for the given context.
        """

        raise NotImplementedError

    def _build_start(self, _log=True):
        """
        Must be called by .build() in the beginning of the build process.
        """

        self.__t0 = time.time()
        try:
            self.syntax_check()
        except SyntaxError as ex:
            self.log('debug', '%s: invalid syntax!' % self.__class__.__name__)
            msg = str(ex)
            raise BuildError(msg)

    def _build_end(self, _log=True):
        """
        Must be called by .build() in the end of the build process.
        """

        self.is_built = True
        self.build_duration = time.time() - self.__t0
        if _log:
            log_is_built(self)

    def close(self):
        """
        Explicitly deallocate all resources allocated by the BuildManager.
        """

        self.is_closed = True

    def to_json(self):
        """
        A JSON compatible representation of object.
        """

        return self.__dict__.copy()

    def syntax_check(self):
        """
        Raise a SyntaxError if source code syntax is invalid.
        """

        raise NotImplementedError

    def get_modules(self):
        """
        Return a list of additional modules that should be pre-loaded by
        box.run() in sandboxed mode.
        """

        return ['ejudge', self.__class__.__module__] + list(self.modules or ())


class IntegratedBuildManager(BuildManager):
    """
    Build context for Python or other languages that can be integrated into
    the main interpreter.

    These languages can provide a locals and a globals dictionary for passing
    symbols to be used during execution.
    """

    def __init__(self, source, locals=None, globals=None, **kwargs):
        super().__init__(source, **kwargs)
        self.locals = locals
        self.globals = globals

    def build(self, _log=True):
        self._build_start(_log)
        self._build_end(_log)


class ExternalProgramBuildManager(BuildManager):
    """
    Build context for compiled programs or programs that run in external
    interpreters. This build context prepares a temporary folder to store all
    necessary files.
    """

    build_path = None
    source_extension = None

    def build(self, _log=True):
        self._build_start(_log)
        self._build_run()
        self._build_end(_log)

    def _build_run(self):
        if not self.build_path:
            self.build_path = self.build_tempdir()
        self.prepare_files()

    def build_tempdir(self):
        """
        Creates a temporary directory for storing files.
        """

        # Make tmp directory readable and writable by everyone, if in sandboxed
        # mode.
        temp_dir = tempfile.mkdtemp()
        if self.is_sandboxed:
            os.chmod(
                temp_dir,
                stat.S_IEXEC | stat.S_IREAD | stat.S_IWRITE |
                stat.S_IXOTH | stat.S_IROTH | stat.S_IWOTH |
                stat.S_IXGRP | stat.S_IRGRP | stat.S_IWGRP
            )

        self.build_path = temp_dir
        self.log('debug', 'temporary build path at %r' % temp_dir)
        return temp_dir

    def write(self, path, data):
        """
        Write contents of the "data" string into the absolute "path".
        """

        if self.build_path is None:
            raise RuntimeError('must create temporary directory first!')

        # Path must be inside the working directory. We block accidental writes
        # on other directories
        if not path.startswith(self.build_path + os.path.sep):
            msg = 'cannot write %r: outside build directory %r'
            msg = msg % (path, self.build_path)
            raise PermissionError(msg)

        full_path = os.path.join(self.build_path, path)

        # Save source
        with open(full_path, 'w') as F:
            F.write(data)

        # If it is going to run inside a sandbox, we have to give very liberal
        # permissions
        if self.is_sandboxed:
            os.chmod(full_path, stat.S_IREAD | stat.S_IROTH | stat.S_IRGRP)
        self.log('debug', '%r successfully created' % path)

    def prepare_files(self):
        """
        Saves all necessary files to the temporary directory.
        """

        filename = self.get_source_filename(absolute=True)
        if not os.path.exists(filename):
            self.write(filename, self.source)
        else:
            raise RuntimeError('file already exist: %r' % filename)

    def get_source_extension(self):
        """
        Return the source file default extension.
        """

        if self.source_extension is None:
            raise NotImplementedError(
                'Subclasses must either define the attribute source_extension '
                'or override the .get_source_extension() method.'
            )
        return self.source_extension

    def get_source_filename(self, absolute=False):
        """
        Return the default source file name.
        """

        ext = self.get_source_extension()
        if not ext:
            name = 'main'
        else:
            name = 'main.' + ext.lstrip('.')
        if absolute:
            return os.path.join(self.build_path, name)
        else:
            return name


class CompiledLanguageBuildManager(ExternalProgramBuildManager):
    """
    Basic support for languages that require a separate compiling step.
    """

    build_args = None
    executable_name = 'main.exe'

    def _build_run(self):
        super()._build_run()
        self.compile_files()

    def compile_files(self):
        self.log('info', 'building: %s' % ' '.join(self.build_args))
        try:
            source_name = self.get_source_filename(absolute=True)
            executable_name = os.path.join(self.build_path,
                                           self.executable_name)
            assert os.path.exists(source_name)
            build_args = self.get_build_args()
            env = os.environ.get
            subprocess.check_output(
                build_args,
                stderr=subprocess.STDOUT,
                timeout=10,
                cwd=self.build_path,
                env={
                    'PATH': env('PATH', '/usr/bin/'),
                    'LANG': env('LANG') or 'C',
                    'LD_LIBRARY_PATH': env('LD_LIBRARY_PATH', '/usr/lib/')
                },
            )

            # Make executable readable and executable by everyone in sandbox
            # mode so the `nobody` can execute this file
            if self.is_sandboxed:
                os.chmod(
                    executable_name,
                    stat.S_IREAD | stat.S_IROTH | stat.S_IRGRP |
                    stat.S_IEXEC | stat.S_IXOTH | stat.S_IXGRP
                )
        except TimeoutError:
            error_msg = 'compilation is taking too long'
            raise BuildError(error_msg)
        except subprocess.CalledProcessError as ex:
            error_msg = ex.output.decode('utf8')
            raise BuildError(error_msg)
        self.log('debug', 'executable created at %r' % executable_name)

    def get_build_args(self):
        """
        Return a list with the build args to be passed to the compiler process.
        """

        if self.build_args is None:
            raise NotImplementedError(
                'Subclasses must either define the .build_args attribute or '
                'override the .get_build_args() method.'
            )

        if isinstance(self.build_args, str):
            import shlex
            return shlex.split(self.build_args)

        return list(self.build_args)


class InterpretedLanguageBuildManager(ExternalProgramBuildManager):
    """
    Basic support for scripting languages and interpreter-like execution.
    """


def log_is_built(manager):
    manager.log('info', 'successfully built (%s sec)' % manager.build_duration)
