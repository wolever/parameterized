"""
A stripped down version of six.py, containing only the bits we actually need.
Kept minimal so that OS package maintainers don't need to patch out six.py.
"""

import sys

PY3 = sys.version_info[0] == 3

if PY3:
    string_types = str,
else:
    string_types = basestring,
