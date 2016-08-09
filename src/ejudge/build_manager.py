import os
import stat
import tempfile

import subprocess

from ejudge.exceptions import BuildError


class BuildManager:
    """
    Stores information about a program build.
    """

    @classmethod
    def from_json(cls, json):
        return cls(**json)

    def __init__(self, source, is_sandboxed=False, modules=None):
        self.source = source
        self.modules = modules
        self.is_sandboxed = is_sandboxed
        self.is_built = False
        self.is_closed = False

    def build(self):
        """
        Prepares build for the given context.
        """

        self.is_built = True

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

    def get_modules(self):
        """
        Return a list of additional modules that should be pre-loaded by
        box.run() in sandboxed mode.
        """

        return (list(self.modules or ())) + [self.__class__.__module__]


class IntegratedBuildManager(BuildManager):
    """
    Build context for Python or other languages that can be integrated into
    the main interpreter.

    These languages can provide a locals and a globals dictionary for passing
    symbols to be used during execution.
    """

    # noinspection PyShadowingBuiltins
    def __init__(self, source, locals=None, globals=None, **kwargs):
        super().__init__(source, **kwargs)
        self.locals = locals
        self.globals = globals


class ExternalProgramBuildManager(BuildManager):
    """
    Build context for compiled programs or programs that run in external
    interpreters. This build context prepares a temporary folder to store all
    necessary files.
    """

    build_path = None
    source_extension = None

    def build(self):
        self.build_path = self.build_tempdir()
        self.prepare_files()
        super().build()

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
        return temp_dir

    def write(self, path, data):
        """
        Write contents of the "data" string into the a "path" relative to the
        working temporary directory.
        """

        if self.build_path is None:
            raise RuntimeError('must create temporary directory first!')

        full_path = os.path.join(self.build_path, path)

        # Save source and make it readable by everyone
        with open(full_path, 'w') as F:
            F.write(data)
        if self.is_sandboxed:
            os.chmod(full_path, stat.S_IREAD | stat.S_IROTH | stat.S_IRGRP)

    def prepare_files(self):
        """
        Saves all necessary files to the temporary directory.
        """

        self.write(self.get_source_filename(), self.source)

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

    def get_source_filename(self):
        """
        Return the default source file name.
        """

        ext = self.get_source_extension()
        if not ext:
            return 'main'
        else:
            return 'main.' + ext.lstrip('.')


class CompiledLanguageBuildManager(ExternalProgramBuildManager):
    """
    Basic support for languages that require a separate compiling step.
    """

    build_args = None
    executable_name = 'main.exe'

    def prepare_files(self):
        super().prepare_files()

        # Compile and return
        current_path = os.getcwd()
        error_msg = 'compilation is taking too long'
        try:
            os.chdir(self.build_path)
            build_args = self.get_build_args()
            error_msg = subprocess.check_output(build_args, timeout=10)

            # Make executable readable and executable by everyone in sandbox
            # mode
            if self.is_sandboxed:
                os.chmod(
                    self.executable_name,
                    stat.S_IREAD | stat.S_IROTH | stat.S_IRGRP |
                    stat.S_IEXEC | stat.S_IXOTH | stat.S_IXGRP
                )

        except (subprocess.CalledProcessError, TimeoutError):
            raise BuildError(error_msg)
        finally:
            # Cannot return to path in sandboxed mode since the nobody user
            # probably does not have read permissions on the old working
            # directory
            if not self.is_sandboxed:
                os.chdir(current_path)

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