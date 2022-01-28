import os
from setuptools import setup, find_packages


version = '0.7.1'


def read(f):
    return open(os.path.join(os.path.dirname(__file__), f)).read().strip()


install_requires = [
    'sdiff @ git+https://github.com/KeepSafe/html-structure-diff.git#egg=sdiff',
    'aiohttp >=3, <3.8',
    'Markdown',
    'parse >=1, <2',
    'beautifulsoup4 >=4, <5',
    'lxml >=3',
]

tests_require = [
    'nose',
    'flake8==3.6.0',
    'coverage',
]

devtools_require = [
    'twine',
    'build',
]

setup(
    name='content-validator',
    version=version,
    description=('Content validator looks at text content and preforms different validation tasks'),
    classifiers=[
        'License :: OSI Approved :: BSD License', 'Intended Audience :: Developers', 'Programming Language :: Python'
    ],
    author='Keepsafe',
    author_email='support@getkeepsafe.com',
    url='https://github.com/KeepSafe/content-validator/',
    license='Apache',
    packages=find_packages(exclude=['tests']),
    package_data={},
    namespace_packages=[],
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={
        'tests': tests_require,
        'devtools': devtools_require,
    },
    entry_points={'console_scripts': ['content-validator = validator:main']},
    include_package_data=False)
