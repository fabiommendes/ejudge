# -*- coding: utf8 -*-
import os

from setuptools import setup, find_packages

# Meta information
name = 'ejudge'
author = 'Fábio Macêdo Mendes'
version = open('VERSION').read().strip()
dirname = os.path.dirname(__file__)

# Save version and author to __meta__.py
with open(os.path.join(dirname, 'src', name, '__meta__.py'), 'w') as F:
    F.write('__version__ = %r\n__author__ = %r\n' % (version, author))

setup(
    # Basic info
    name=name,
    version=version,
    author=author,
    author_email='fabiomacedomendes@gmail.com',
    url='http://github.com/fabiommendes/ejudge',
    description='A simple ejudge for Python. Supports several languages and '
                'sandboxing.',
    long_description=open('README.rst').read(),

    # Classifiers (see https://pypi.python.org/pypi?%3Aaction=list_classifiers)
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Education',
        'Topic :: Software Development :: Libraries',
    ],

    # Packages and depencies
    package_dir={'': 'src'},
    packages=find_packages('src'),
    install_requires=[
        'psutil',
        'pexpect',
        'iospec>=0.3',
        'boxed>=0.3'
    ],
    extras_require={
        'dev': [
            'pytest',
            'python-boilerplate',
        ],
    },

    # Scripts
    entry_points={
       'console_scripts': ['ejudge = ejudge.__main__:main'],
    },

    # Other configurations
    zip_safe=False,
    platforms='any',
)
