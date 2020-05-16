import re
import ast

from setuptools import setup


_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('bkp891/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

setup(
    name='bkp891',
    version=version,
    description='BK Precision 891 Python Library/Driver',
    url='https://github.com/jpunkt/bk891.git',
    download_url='https://github.com/jpunkt/bk891/tarball/{0}'.format(version),
    license='MIT',
    author='Johannes Payr',
    author_email='johannes@arg-art.org',
    packages=[str('bkp891')],
    platforms='any',
    install_requires=['pyserial>=2.6']
)
