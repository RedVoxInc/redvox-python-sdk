from setuptools import setup, find_packages

with open("requirements.txt", "r") as requirements_file:
    requirements = list(map(lambda line: line.strip(), requirements_file.readlines()))

setup(name='redvox',
    version='1.1.0',
    url='https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/',
    license='Apache',
    author='RedVox',
    author_email='dev@redvoxsound.com',
    description='Library for working with RedVox files.',
    packages=find_packages(include=["redvox", "redvox.api900", "redvox.api900.lib"], exclude=['tests']),
    long_description=open('README.md').read(),
    install_requires=requirements,
    python_requires=">=3.6")
