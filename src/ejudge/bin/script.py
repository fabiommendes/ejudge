'''
Created on 29/09/2015

@author: chips
'''
import os
import argparse
from collections import namedtuple
from judge import graders

Grade = namedtuple('Grade', ['value', 'message'])


def parser():
    '''Returns the parser object for script.'''

    parser = argparse.ArgumentParser(
        description='Automatically grade the input file')
    parser.add_argument('file', help='input file to grade')
    parser.add_argument('--template', '-t',
                        help='grader template file')
    parser.add_argument('--grade', '-g', action='store_true',
                        help=('simply return the final grade without '
                              'showing messages'))
    return parser


def gradefile(src, template, ext=None, timeout=5.0):
    '''Return a Grade object corresponding to the given grading job'''

    template = template.read()
    src_ext = ext or os.path.splitext(src.name)[1]
    src = src.read()

    if src_ext == '.py':
        result = graders.grade_pycode(src, template, timeout=timeout)
        grade = result.get_grade()
        message = result.feedback(format='text')
        return Grade(grade, message)
    else:
        msg = 'file with extension %s is not supported' % src_ext
        raise ValueError(0, msg)


def main():
    '''Executes the main script'''

    # Fetch parameters from argparse
    args = parser().parse_args()
    src = args.file
    template = args.template
    grade_only = args.grade
    if template is None:
        template = os.path.splitext(src)[0] + '.io'

    try:
        with open(src) as src_data:
            with open(template) as template_data:
                grade = gradefile(src_data, template_data)
    except Exception as ex:
        # Handle errors
        if ex.args[0] == 0:
            print('Error:', ex)
            raise SystemExit
        else:
            value = input('An unknown error was found, '
                          'do you wish to see the traceback? [y/N] ')

            ex = ex if value.lower() in ['y', 'yes'] else SystemExit
            raise ex

    if not grade_only and grade.message:
        print(grade.message)
    if grade.value == 1:
        print('Final grade: 100%, congratulations!')
    else:
        print('Final grade: %s%%' % (grade.value * 100))
