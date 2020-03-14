from setuptools import setup, find_packages

import redvox

with open("requirements.txt", "r") as requirements_file:
    requirements = list(map(lambda line: line.strip(), requirements_file.readlines()))

setup(name=redvox.NAME,
      version=redvox.VERSION,
      url='https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/',
      license='Apache',
      author='RedVox',
      author_email='dev@redvoxsound.com',
      description='Library for working with RedVox files.',
      packages=find_packages(include=["redvox",
                                      "redvox.api900",
                                      "redvox.api900.lib",
                                      "redvox.api900.sensors",
                                      "redvox.api900.timesync",
                                      "redvox.api900.qa",
                                      "redvox.cli",
                                      "redvox.common"],
                             exclude=['tests']),
      long_description=open('README.md').read(),
      install_requires=requirements,
      entry_points={
            'console_scripts': ['redvox-cli=redvox.cli.cli:main']
      },
      python_requires=">=3.6")
