import os
from setuptools import setup, find_packages

version = '1.0.0'


def read(f):
    return open(os.path.join(os.path.dirname(__file__), f)).read().strip()


install_requires = [
    'sdiff @ git+https://github.com/KeepSafe/html-structure-diff.git@1.0.0#egg=sdiff',
    'aiohttp==3.8.5',
    'Markdown',
    'parse <= 1.8.2',
    'beautifulsoup4 >=4, <5',
    'lxml<5',
]

tests_require = [
    'pytest >= 8',
    'coverage==7.6.1',
    'flake8==7.1.1',
]

devtools_require = [
    'twine',
    'build',
]

setup(
    name='content-validator',
    version=version,
    python_requires='>=3.11',
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
