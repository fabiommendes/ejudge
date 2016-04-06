from ejudge.langs import CompiledLanguage


#
# C compilers
#
# We have manager classes for the two biggest compilers gcc and clang and also
# for tcc, the tiny C compiler, which is a small and fast compiler. In the
# future we might create an IntegratedManager based on clang or tcc or even on
# a C interpreter like ROOT's Cint.
#
class CLanguage(CompiledLanguage):
    abstract = True

    def syntax_check(self):
        pass


class TccManager(CLanguage):
    name = 'tcc'
    description = 'ANSI C (tcc)'
    extension = 'c'
    extensions = []
    buildargs = ['tcc', '-w', '-o', 'main.exe', 'main.c']


class GccManager(CLanguage):
    name = 'gcc'
    description = 'C99 (gcc)'
    extension = 'c'
    extensions = ['c']
    buildargs = ['gcc', '-lm', 'main.c', '-o', 'main.exe']


class ClangManager(CLanguage):
    name = 'clang'
    description = 'ANSI C (tcc)'
    extension = 'c'
    extensions = []
    buildargs = ['clang', '-lm', '-o', 'main.c', '-o', 'main.exe']


#
# C++ compilers
#
class CppLanguage(CompiledLanguage):
    abstract = True

    def syntax_check(self):
        pass


class GccCppManager(CppLanguage):
    name = 'g++'
    description = 'C++11 (gcc)'
    extension = 'cpp'
    extensions = ['cpp']
    buildargs = ['g++', '-lm', '-o', 'main.cpp', '-o', 'main.exe']


class ClangCppManager(CppLanguage):
    name = 'clang-c++'
    description = 'ANSI C (tcc)'
    extension = 'cpp'
    extensions = []
    buildargs = ['clang', '-lm', '-o', 'main.cpp', '-o', 'main.exe']
