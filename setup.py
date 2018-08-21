import os
from setuptools import setup, find_packages


version = '0.6.0'


def read(f):
    return open(os.path.join(os.path.dirname(__file__), f)).read().strip()


install_requires = [
    'aiohttp >=3, <3.4',
    'Markdown >=2, <3',
    'parse >=1, <2',
    'beautifulsoup4 >=4, <5',
    'lxml >=3, <4',
]

setup(
    name='content-validator',
    version=version,
    description=('Content validator looks at text content and preforms different validation tasks'),
    long_description='\n\n'.join((read('README.md'), read('CHANGELOG'))),
    classifiers=[
        'License :: OSI Approved :: BSD License', 'Intended Audience :: Developers', 'Programming Language :: Python'
    ],
    author='Keepsafe',
    author_email='support@getkeepsafe.com',
    url='https://github.com/KeepSafe/google-play-cmd/',
    license='Apache',
    packages=find_packages(exclude=['tests']),
    package_data={},
    namespace_packages=[],
    install_requires=install_requires,
    entry_points={'console_scripts': ['content-validator = validator:main']},
    include_package_data=False)
