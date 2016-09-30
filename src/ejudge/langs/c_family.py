import subprocess
import tempfile

import shutil

from ejudge.build_manager import CompiledLanguageBuildManager
from ejudge.execution_manager import CompiledLanguageExecutionManager


#
# C compilers
#
# We have manager classes for the two biggest compilers gcc and clang and also
# for tcc, the tiny C compiler, which is a small and fast compiler. In the
# future we might create an IntegratedManager based on clang or tcc or even on
# a C interpreter like ROOT's Cint.
#
class CLanguageBuildManager(CompiledLanguageBuildManager):
    """
    Common functionality for all C-based builders.
    """

    source_extension = '.c'
    language = 'c'
    shell_checker_args = ['gcc', '-fsyntax-only']

    def syntax_check(self):
        c_syntax_check(self.source, compiler='gcc')


class CLanguageExecutionManager(CompiledLanguageExecutionManager):
    """
    Execution manager for all C-based languages.
    """


class GccBuildManager(CLanguageBuildManager):
    """
    Build executable with GCC.
    """

    language = 'c'
    build_args = ['gcc', '-lm', 'main.c', '-std=c99', '-o', 'main.exe']


class TccBuildManager(CLanguageBuildManager):
    """
    Build executable with TCC.
    """

    language = 'tcc'
    build_args = ['tcc', '-w', '-o', 'main.exe', 'main.c']

    def syntax_check(self):
        c_syntax_check(self.source, compiler='tcc')


class ClangBuildManager(CLanguageBuildManager):
    """
    Build executable with Clang compiler.
    """

    language = 'clang'
    build_args = ['clang', '-lm', 'main.c', '-std=c99', '-o', 'main.exe']

    def syntax_check(self):
        c_syntax_check(self.source, compiler='clang')


#
# C++ compilers
#
class CppBuildManager(CompiledLanguageBuildManager):
    """
    Base class for C++ builders.
    """

    source_extension = '.cpp'
    language = 'c++'


class GccCppBuildManager(CppBuildManager):
    """
    Build executable with g++
    """

    language = 'g++'
    build_args = ['g++', '-lm', '-o', 'main.cpp', '-o', 'main.exe']

    def syntax_check(self):
        c_syntax_check(self.source, compiler='g++', cpp=True)


class ClangCppBuildManager(CppBuildManager):
    """
    Build executable from C++ source with clang.
    """

    language = 'clang++'
    build_args = ['clang++', '-lm', '-o', 'main.cpp', '-o', 'main.exe']

    def syntax_check(self):
        c_syntax_check(self.source, compiler='clang++', cpp=True)


def c_syntax_check(source, compiler=None, cpp=False, encoding='utf8'):
    """
    Check syntax of C code.

    Raises a SyntaxError on error. Do not return anything.

    Args:
        source (str):
            A string with C or C++ source code.
        compiler (optional, str or list):
            One of {clang, gcc, tcc} (or their corresponding C++ counterparts)
            or a list of priorities.
        cpp (bool):
            Set to true for C++ syntax check.
        encoding (str):
            Encoding for the program source.
    """

    compilers_c = ['clang', 'gcc', 'tcc']
    compilers_cpp = ['clang++', 'g++']
    compilers = compilers_cpp if cpp else compilers_c

    # Create list of compilers by priority
    if isinstance(compiler, str):
        if compiler not in compilers:
            raise ValueError('invalid compiler: %r' % compiler)

        compilers.pop(compilers.index(compiler))
        compilers = [compiler] + compilers
    elif compiler is not None:
        compiler = list(compiler)

        for comp_item in compiler:
            if comp_item not in compilers:
                raise ValueError('invalid compiler: %r' % compiler)

        compiler.extend(x for x in compilers if x not in compiler)
        compilers = compiler

    # Find the first compiler executable installed in the system
    for compiler in compilers:
        compiler_path = shutil.which(compiler)
        if compiler_path:
            break
    else:
        msg = 'no suitable compiler found from list %r' % compilers
        raise RuntimeError(msg)

    # Open a temporary file and execute ``CC -fsytnax-only source.c``
    with tempfile.NamedTemporaryFile(mode='w',
                                     suffix='.cpp' if cpp else '.c',
                                     encoding=encoding,
                                     delete=False) as F:
        F.write(source)
        F.flush()
        cmd = [compiler_path, '-fsyntax-only', F.name, '-o', '/dev/null']

        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            out = None
        except subprocess.CalledProcessError as ex:
            out = ex.output.decode('utf8') or 'syntax error'

    if out is not None:
        raise SyntaxError(out)
