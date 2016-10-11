import argparse

import ejudge
import iospec
from ejudge import __version__


def make_parser():
    """
    Creates parser object.
    """

    parser = argparse.ArgumentParser(
        description='Automatically grade the input file',
    )
    parser.add_argument('--version', '-v', action='version',
                        version='%(prog)s' + __version__)
    subparsers = parser.add_subparsers(
        title='subcommands',
        description='valid subcommands',
    )

    # ejudge run <source> ...
    run_parser = subparsers.add_parser(
        'run', help='run program defined by source code'
    )
    run_parser.add_argument('file', help='input source code')
    run_parser.add_argument(
        '--inputs', '-r',
        help='a file with raw inputs to run with the program'
    )
    run_parser.add_argument(
        '--iospec', '-i',
        help='a file with iospec interactions to test with the program'
    )
    run_parser.set_defaults(func=command_run)

    # ejudge grade <source> <inputs>
    grade_parser = subparsers.add_parser(
        'grade',
        help='grade program with the selected inputs'
    )
    grade_parser.add_argument('file', help='input source code')
    grade_parser.add_argument('inputs', help='IoSpec interaction')
    grade_parser.set_defaults(func=command_grade)

    return parser


def command_run(args):
    """
    Implements "ejudge run <source> <inputs>" command.
    """

    source, lang = get_source_and_lang(args.file)
    if args.iospec:
        with open(args.iospec) as F:
            input_data = iospec.parse(F)
    elif args.inputs:
        with open(args.inputs) as F:
            input_data = F.read()
        if input_data.endswith('\n'):
            input_data = input_data[:-1]
        input_data = input_data.splitlines()
    else:
        with open(args.file) as F:
            source = F.read()
        lang = ejudge.registry.language_from_filename(args.file)
        ejudge.exec(source, lang=lang)
        return

    result = ejudge.run(source, input_data, lang=lang)
    print(result.source())


def command_grade(args):
    """
    Implements "ejudge grade <source> <inputs>" command.
    """

    source, lang = get_source_and_lang(args.file)
    input_data = iospec.parse(args.inputs)
    feedback = ejudge.grade(source, input_data, lang=lang)
    print(feedback.as_text())


def get_source_and_lang(path):
    """
    Return a tuple with (source, lang) for the given input file path.
    """

    with open(path) as F:
        source = F.read()
    lang = ejudge.registry.language_from_filename(path)
    return source, lang


def main():
    """
    Executes the main script.
    """

    parser = make_parser()
    args = parser.parse_args()
    try:
        func = args.func
    except AttributeError:
        print('Type `ejudge --help` for usage.')
    else:
        func(args)

if __name__ == '__main__':
    main()
