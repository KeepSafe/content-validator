import os
from setuptools import setup, find_packages
from pip.req import parse_requirements

version = '0.0.1'


def read(f):
    return open(os.path.join(os.path.dirname(__file__), f)).read().strip()

install_reqs = parse_requirements('requirements.txt')
reqs = [str(ir.req) for ir in install_reqs]


setup(name='content-validator',
      version=version,
      description=('Content validator looks at text content and preforms different validation tasks'),
      long_description='\n\n'.join((read('README.md'), read('CHANGELOG'))),
      classifiers=[
          'License :: OSI Approved :: BSD License',
          'Intended Audience :: Developers',
          'Programming Language :: Python'],
      author='Keepsafe',
      author_email='support@getkeepsafe.com',
      url='https://github.com/KeepSafe/google-play-cmd/',
      license='Apache',
      packages=find_packages('src', exclude=['test']),
      py_modules=['validator', 'url', 'utils'],
      package_dir = {'': 'src'},
      package_data={},
      namespace_packages=[],
      install_requires = reqs,
      entry_points={
          'console_scripts': [
              'content-validator = validator:main']
      },
      include_package_data = False)
