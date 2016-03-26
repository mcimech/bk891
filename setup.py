import re
import ast

from setuptools import setup


_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('bkp879b/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

setup(
    name='bkp879b',
    version=version,
    description='BK Precision 879B/878B Python Library/Driver',
    url='https://github.com/jimbattin/bkp879b',
    download_url='https://github.com/jimbattin/bkp879b/tarball/{0}'.format(version),
    license='MIT',
    author='Jim Battin',
    author_email='jrbattin@gmail.com',
    packages=[str('bkp879b')],
    platforms='any',
    install_requires=['pyserial>=2.6']
)
