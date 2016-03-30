import os
import setuptools
from setuptools import setup

#
# Read VERSION from file and write it in the appropriate places
#
AUTHOR = 'Fábio Macêdo Mendes'
BASE, _ = os.path.split(__file__)
with open(os.path.join(BASE, 'VERSION')) as F:
    VERSION = F.read().strip()
with open(os.path.join(BASE, 'src', 'ejudge', 'meta.py'), 'w') as F:
    F.write(
        '# Auto-generated file. Please do not edit\n'
        '__version__ = %r\n' % VERSION +
        '__author__ = %r\n' % AUTHOR)

VERSION_BIG = VERSION.rpartition('.')[0]

#
# Main configuration script
#
setup(
    name='ejudge',
    version=VERSION,
    description='An automatic judge for grading code',
    author='Fábio Macêdo Mendes',
    author_email='fabiomacedomendes@gmail.com',
    url='https://github.com/fabiommendes/pyjudge',
    long_description=open(os.path.join(BASE, 'README.txt')).read(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
    ],

    package_dir={'': 'src'},
    packages=setuptools.find_packages('src'),
    package_data={
        '': ['*.*'],
    },
    license='GPL',
    zip_safe=False,
    install_requires=['psutil', 'pexpect',
                      'iospec>=0.1.3', 'boxed>=0.1.3.1'],
    entry_points={
        'console_scripts': ['pyjudge = judge.bin.judge:main'],
    },
)
