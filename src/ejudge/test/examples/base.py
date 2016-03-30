import io
import os
import unittest
import functools
from judge.bin.script import gradefile
from judge.tests.examples.simple_template import template as simple_template


class TestSimpleExamples(unittest.TestCase):

    def test_simple(self):
        path = os.path.join(basepath, 'simple.py')
        with open(path) as F:
            grade = gradefile(F, io.StringIO(simple_template), '.py')
        assert grade.message is None, grade
        assert grade.value == 1, grade


basepath = os.path.split(__file__)[0]
for suffix in ['build', 'extrainput', 'presentation', 'timeout', 'unexpected',
               'unusedinput', 'wrong']:

    with open(os.path.join(basepath, 'simple_%s.py' % suffix)) as F:
        src = F.read()

    with open(os.path.join(basepath, 'simple_%s.txt' % suffix)) as F:
        response = F.read()
        response = '\n'.join(response.splitlines()[:-1])

    def method(src, response):
        src = io.StringIO(src)
        template = io.StringIO(simple_template)
        grade = gradefile(src, template, '.py', timeout=0.5)
        msg = '\nGot:\n\n%s\n\nExpect:\n %s' % (grade.message, response)
        assert grade.message == response, msg
        assert grade.value == 0, grade

    method = functools.partial(method, src, response)
    method_name = 'test_%s' % suffix
    setattr(TestSimpleExamples, method_name, method)


if __name__ == '__main__':
    TestSimpleExamples.test_simple(None)
    TestSimpleExamples.test_wrong()
