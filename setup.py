# -*- coding: utf-8 -*-
#
# This file were created by Python Boilerplate. Use boilerplate to start simple
# usable and best-practices compliant Python projects.
#
# Learn more about it at: http://github.com/fabiommendes/python-boilerplate/
#

import os
import codecs
from setuptools import setup, find_packages

# Save version and author to __meta__.py
version = open('VERSION').read().strip()
dirname = os.path.dirname(__file__)
path = os.path.join(dirname, 'src', 'ejudge', '__meta__.py')
meta = '''# Automatically created. Please do not edit.
__version__ = u'%s'
__author__ = u'F\\xe1bio Mac\\xeado Mendes'
''' % version
with open(path, 'w') as F:
    F.write(meta)

setup(
    # Basic info
    name='ejudge',
    version=version,
    author='Fábio Macêdo Mendes',
    author_email='fabiomacedomendes@gmail.com',
    url='http://github.com/fabiommendes/ejudge',
    description='A simple ejudge for Python. Supports several languages and '
                'sandboxing.',
    long_description=codecs.open('README.rst', 'rb', 'utf8').read(),

    # Classifiers (see https://pypi.python.org/pypi?%3Aaction=list_classifiers)
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries',
    ],

    # Packages and dependencies
    package_dir={'': 'src'},
    packages=find_packages('src'),
    install_requires=[
        'lazyutils',
        'iospec>=0.3.11',
        'boxed>=0.3.9'
    ],
    extras_require={
        'dev': [
            'python-boilerplate',
            'invoke>=0.13',
            'pytest',
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
