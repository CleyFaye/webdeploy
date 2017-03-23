#!/usr/bin/env python
# encoding=utf-8
import os
from setuptools import setup


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="web_deploy",
    version="0.0",
    author="Gabriel Paul 'Cley Faye' Risterucci",
    author_email="gabriel.risterucci@gmail.com",
    description=("A basic tool to automate the tasks involved in deploying a"
                 "Django web project into a runtime directory"),
    license="MIT",
    keywords="deploy django make",
    url="https://repos.cleyfaye.net/trac/WebDeploy",
    py_modules=['webdeploy'],
    packages=[
        'wdeploy',
        'wdeploy.tasks',
    ],
    entry_points={
        'console_scripts': [
            'webdeploy=webdeploy:main'
        ],
    },
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
    ],
)
