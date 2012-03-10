#!/usr/bin/env python

import os
import sys

from setuptools import setup, find_packages

os.chdir(os.path.dirname(sys.argv[0]) or ".")

setup(
    name="nose-parameterized",
    version="0.1",
    url="https://github.com/wolever/nose-parameterized",
    author="David Wolever",
    author_email="david@wolever.net",
    description="Nose decorator for parameterized testing",
    packages=find_packages(),
)
