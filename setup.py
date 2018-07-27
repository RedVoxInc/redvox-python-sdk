from setuptools import setup, find_packages

with open("requirements.txt", "r") as requirements_file:
    requirements = list(map(lambda line: line.strip(), requirements_file.readlines()))
    setup(name='redvox',
          version='0.6',
          url='https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/',
          license='Apache',
          author='RedVox',
          author_email='dev@redvoxsound.com',
          description='Library for working with RedVox files.',
          packages=find_packages(include=["redvox", "redvox.api900", "redvox.api900.lib"], exclude=['tests']),
          long_description=open('README.md').read(),
          install_requirements=requirements,
          zip_safe=False)
