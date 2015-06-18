#!/usr/bin/env python

import os
import sys

from setuptools import setup, find_packages

os.chdir(os.path.dirname(sys.argv[0]) or ".")

setup(
    name="nose-parameterized",
    version="0.4.1",
    url="https://github.com/wolever/nose-parameterized",
    author="David Wolever",
    author_email="david@wolever.net",
    description="Decorator for parameterized testing with Nose",
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: BSD License',
    ],
    packages=find_packages(),
)
