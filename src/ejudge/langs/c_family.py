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

    def syntax_check(self):
        return NotImplemented


class CLanguageExecutionManager(CompiledLanguageExecutionManager):
    """
    Execution manager for all C-based languages.
    """


class GccBuildManager(CLanguageBuildManager):
    """
    Build executable with GCC.
    """

    build_args = ['gcc', '-lm', 'main.c', '-std=c99', '-o', 'main.exe']


class TccBuildManager(CLanguageBuildManager):
    """
    Build executable with TCC.
    """

    build_args = ['tcc', '-w', '-o', 'main.exe', 'main.c']


class ClangBuildManager(CLanguageBuildManager):
    """
    Build executable with Clang compiler.
    """

    build_args = ['clang', '-lm', 'main.c', '-std=c99', '-o', 'main.exe']


#
# C++ compilers
#
class CppBuildManager(CompiledLanguageBuildManager):
    """
    Base class for C++ builders.
    """

    source_extension = '.cpp'

    def syntax_check(self):
        pass


class GccCppBuildManager(CppBuildManager):
    """
    Build executable with g++
    """

    build_args = ['g++', '-lm', '-o', 'main.cpp', '-o', 'main.exe']


class ClangCppBuildManager(CppBuildManager):
    """
    Build executable from C++ source with clang.
    """

    build_args = ['clang', '-lm', '-o', 'main.cpp', '-o', 'main.exe']
