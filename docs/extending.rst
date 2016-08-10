Supporting other languages
==========================

For support for other languages it is necessary to subclass both
:class:`ejudge.build_manager.BuildManager`, and :class:`ejudge.execution_manager.ExecutionManager`.
Ejudge implements subclasses for the common cases of a programming language with a compile-run cycle
and that of a interpreted/scripting language.

Compiled languages
------------------

It is most convenient to subclass :class:`ejudge.build_manager.CompiledLanguageBuildManager`
and :class:`ejudge.execution_manager.CompiledLanguageExecutionManager`. The first class is
responsible for building the executable file, which by default should be named
``main.exe``. The build manager also produces a temporary directory used to
compile and store the source code.

Subclass should provide at least the file extension, the compiler command and a
function to check syntax::

    from ejudge.build_manager import CompiledLanguageBuildManager


    class CBuildManager(CompiledLanguageBuildManager):
        source_extension = '.c'
        build_args = ['gcc', '-lm', 'main.c', '-std=c99', '-o', 'main.exe']

        def syntax_check(self):
            if not is_valid_c_syntax(self.source):
                # In reality we should tell something about line numbers and
                # specific errors in the message string passed to SyntaxError.
                raise SyntaxError('invalid C syntax!')

The ExecutionManager doesn't have to provide any information, hence we simply
subclass it without overriding any method::

    from ejudge.execution_manager import CompiledLanguageExecutionManager


    class CExecutionManager(CompiledLanguageExecutionManager):
        pass

Finally, we have to register these classes in the global registry::

    from ejudge import registry

    registry.register(
        'c',
        CBuildManager,       # Can use the full Python path, instead
        CExecutionManager,   # The same here...
        aliases=['gcc', 'C', 'cc'],
        extensions=['.c'],
    )


Interpreted Languages
---------------------

Now we should subclass :class:`ejudge.build_manager.InterpretedLanguageBuildManager`
and :class:`ejudge.execution_manager.InterpretedLanguageExecutionManager`.

The build manager for interpreted languages is slightly more simple since we do
not have a build command::

    from ejudge.build_manager import InterpretedLanguageBuildManager


    class RubyBuildManager(InterpretedLanguageBuildManager):
        source_extension = '.rb'

        def syntax_check(self):
            if not is_valid_ruby_syntax(self.source):
                raise SyntaxError('invalid ruby syntax!')

The ExecutionManager has to know the interpreter name. We assume that the
interpreter is called as ``interpreter <source_file>``. If the calling sequence
is different, we should override the ``shell_args`` variable instead of
``interpreter_command``::

    from ejudge.execution_manager import InterpretedLanguageExecutionManager


    class RubyExecutionManager(InterpretedLanguageExecutionManager):
        interpreter_command = 'ruby'

We have to register these classes in the global registry as before::

    from ejudge import registry

    registry.register(
        'ruby',
        RubyBuildManager,       # Can use the full Python path, instead
        RubyExecutionManager,   # The same here...
        aliases=['rb'],
        extensions=['.rb'],
    )

