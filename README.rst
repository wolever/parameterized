Parameterized testing with any Python test framework
====================================================

DEPRECATION WARNING
-------------------

The ``nose-parameterized`` package is deprecated and has been renamed to ``parameterized``.

See:

- https://pypi.python.org/pypi/parameterized
- https://github.com/wolever/parameterized


Migrating from ``nose-parameterized`` to ``parameterized``
----------------------------------------------------------

To migrate a codebase from ``nose-parameterized`` to ``parameterized``:

1. Update the requirements file, replacing ``nose-parameterized`` with
   ``parameterized``.

2. Replace all references to ``nose_parameterized`` with ``parameterized``::

    $ perl -pi -e 's/nose_parameterized/parameterized/g' your-codebase/

3. You're done!
