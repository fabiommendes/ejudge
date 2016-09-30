from ejudge.registry_class import registry


# C family languages
registry.register(
    'c',
    'ejudge.langs.c_family.GccBuildManager',
    'ejudge.langs.c_family.CLanguageExecutionManager',
    extensions=['.c'],
    aliases=['gcc', 'C', 'cc']
)
registry.register(
    'tcc',
    'ejudge.langs.c_family.TccBuildManager',
    'ejudge.langs.c_family.CLanguageExecutionManager',
)
registry.register(
    'clang',
    'ejudge.langs.c_family.ClangBuildManager',
    'ejudge.langs.c_family.CLanguageExecutionManager',
)
registry.register(
    'c++',
    'ejudge.langs.c_family.GccCppBuildManager',
    'ejudge.langs.c_family.CLanguageExecutionManager',
    extensions=['.cpp', '.c++'],
    aliases=['cpp', 'g++', 'C++']
)
registry.register(
    'clang++',
    'ejudge.langs.c_family.ClangCppBuildManager',
    'ejudge.langs.c_family.CLanguageExecutionManager',
    aliases=['clang++']
)


# Python family
registry.register(
    'python',
    'ejudge.langs.python_family.PythonBuildManager',
    'ejudge.langs.python_family.PythonExecutionManager',
    extensions=['.py', 'py3'],
    aliases=['python3', 'python3x', 'python3.x', 'py', 'py3', 'py3x', 'py3.x']
)
registry.register(
    'python2',
    'ejudge.langs.python_family.Python2BuildManager',
    'ejudge.langs.python_family.Python2ExecutionManager',
    extensions=['.py2'],
    aliases=['python27', 'python2.7', 'py2', 'py27']
)
registry.register(
    'python-script',
    'ejudge.langs.python_family.PythonScriptBuildManager',
    'ejudge.langs.python_family.PythonScriptExecutionManager',
)


# Other scripting languages
registry.register(
    'ruby',
    'ejudge.langs.ruby.RubyBuildManager',
    'ejudge.langs.ruby.RubyExecutionManager',
    extensions=['.rb'],
    aliases=['rb'],
)


# Exotic and special purpose languages
registry.register(
    'pytuga',
    'ejudge.langs.pytuga.PytugaBuildManager',
    'ejudge.langs.pytuga.PytugaExecutionManager',
    extensions=['.pytg'],
    aliases=['pytg', 'pytugues', 'pytuguês']
)
