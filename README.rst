`ejudge` is a library that implements a basic eletronic judge/grader for code.
It can run Python, Ruby, C, and C++ code in a sandbox and supporting other
languages is easy.

This library uses the ``iospec`` format for specifying the expected inputs and
outputs for the some program execution. For more info, refer to the `iospec`_
manual.


Command line
============

The ``ejudge`` command creates


Library
=======

The main entry points in the :mod:`ejudge` module are the :func:`ejudge.run` and
:func:`ejudge.grade` functions. The first is responsible for running code against
a set of inputs and collect the resulting IO. The second function runs code and
compares it with the expected iospec result.

.. autofunction::ejudge.run

.. autofunction::ejudge.grade



Supporting other languages
==========================

For support for other languages it is necessary to subclass both
:cls:`ejudge.BuildManager`, and :cls:`ejudge.ExecutionManager`. Ejudge implements
subclasses for the common cases of a programming language with a compile-run cycle
and that of a interpreted/scripting language.

Compiled languages
------------------

It is most convenient to subclass :cls:`ejudge.CompiledLanguageBuildManager`
and :cls:`ejudge.CompiledLanguageExecutionManager`. The first class is
responsible for building the executable file, which by default should be named
``main.exe``.

Usually, users
should start with either  or :cls:`ejudge.InterpretedLanguageBuildManager`,
depending on the sittuation.