`ejudge` is a library that implements a basic electronic judge/grader for code.
It can run Python, Ruby, C, and C++ code in a sandbox and supporting other
languages is easy.

This library uses the ``iospec`` format for specifying the expected inputs and
outputs for the some program execution. For more info, refer to the iospec_
manual.

.. _iospec: https://readthedocs.org/iospec/


Command line
============

The ``ejudge`` accepts two sub-commands:

``$ ejudge run <source> <inputs>``:
    Runs the given input source code and passes all inputs defined
    in the <inputs> file. The inputs may be either a simple text file with one
    input per line or an IoSpec source file with an `.iospec` extension.
``$ ejudge grade <source> <iospec inputs>``:
    Runs the input source code and compares the result with the given IoSpec
    test cases. It than returns a feedback message telling if the code ran as
    expected and, in case of errors, what are the probable problems.

Library
=======

The main entry points in the :mod:`ejudge` module are the :func:`ejudge.run` and
:func:`ejudge.grade` functions. The first is responsible for running code against
a set of inputs and collect the resulting IO. The second function runs code and
compares it with the expected iospec result.

>>> from ejudge import run
>>> src = 'print("hello %s!" % input("name: "))'
>>> inputs = ['john']
>>> spec = run(src, inputs, lang='python')
>>> list(spec[0])  # fetch the first test case
[Out('name: '), In('john'), Out('hello john!')]
