from setuptools import setup, find_packages

setup(name='redvox',
      version='0.2',
      url='https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/',
      license='Apache',
      author='RedVox',
      author_email='dev@redvoxsound.com',
      description='Library for working with RedVox files.',
      packages=find_packages(exclude=['tests']),
      long_description=open('README.md').read(),
      zip_safe=False)