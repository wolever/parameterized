#!/usr/bin/env python

import os
import sys

from setuptools import setup, find_packages

os.chdir(os.path.dirname(sys.argv[0]) or ".")

setup(
    name="nose-parameterized",
    version="0.2",
    url="https://github.com/wolever/nose-parameterized",
    author="David Wolever",
    author_email="david@wolever.net",
    description="Nose decorator for parameterized testing",
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3'
    ],
    packages=find_packages(),
)
