Parameterized testing with any Python test framework
====================================================

.. image:: https://travis-ci.org/wolever/parameterized.svg?branch=master
    :target: https://travis-ci.org/wolever/parameterized

Parameterized testing in Python sucks.

``parameterized`` fixes that. For everything. Parameterized testing for nose,
parameterized testing for py.test, parameterized testing for unittest.

.. code:: python

    # test_math.py
    from nose.tools import assert_equal
    from parameterized import parameterized

    import unittest
    import math

    @parameterized([
        (2, 2, 4),
        (2, 3, 8),
        (1, 9, 1),
        (0, 9, 0),
    ])
    def test_pow(base, exponent, expected):
        assert_equal(math.pow(base, exponent), expected)

    class TestMathUnitTest(unittest.TestCase):
        @parameterized.expand([
            ("negative", -1.5, -2.0),
            ("integer", 1, 1.0),
            ("large fraction", 1.6, 1),
        ])
        def test_floor(self, name, input, expected):
            assert_equal(math.floor(input), expected)

With nose (and nose2)::

    $ nosetests -v test_math.py
    test_math.test_pow(2, 2, 4) ... ok
    test_math.test_pow(2, 3, 8) ... ok
    test_math.test_pow(1, 9, 1) ... ok
    test_math.test_pow(0, 9, 0) ... ok
    test_floor_0_negative (test_math.TestMathUnitTest) ... ok
    test_floor_1_integer (test_math.TestMathUnitTest) ... ok
    test_floor_2_large_fraction (test_math.TestMathUnitTest) ... ok

    ----------------------------------------------------------------------
    Ran 7 tests in 0.002s

    OK

As the package name suggests, nose is best supported and will be used for all
further examples.

With py.test (version 2.0 and above)::

    $ py.test -v test_math.py
    ============================== test session starts ==============================
    platform darwin -- Python 2.7.2 -- py-1.4.30 -- pytest-2.7.1
    collected 7 items

    test_math.py::test_pow::[0] PASSED
    test_math.py::test_pow::[1] PASSED
    test_math.py::test_pow::[2] PASSED
    test_math.py::test_pow::[3] PASSED
    test_math.py::TestMathUnitTest::test_floor_0_negative
    test_math.py::TestMathUnitTest::test_floor_1_integer
    test_math.py::TestMathUnitTest::test_floor_2_large_fraction

    =========================== 7 passed in 0.10 seconds ============================

With unittest (and unittest2)::

    $ python -m unittest -v test_math
    test_floor_0_negative (test_math.TestMathUnitTest) ... ok
    test_floor_1_integer (test_math.TestMathUnitTest) ... ok
    test_floor_2_large_fraction (test_math.TestMathUnitTest) ... ok

    ----------------------------------------------------------------------
    Ran 3 tests in 0.000s

    OK

(note: because unittest does not support test decorators, only tests created
with ``@parameterized.expand`` will be executed)

Installation
------------

::

    $ pip install parameterized


Compatibility
-------------

`Yes`__.

__ https://travis-ci.org/wolever/parameterized

.. list-table::
   :header-rows: 1
   :stub-columns: 1

   * -
     - Py2.6
     - Py2.7
     - Py3.3
     - Py3.4
     - PyPy
   * - nose
     - yes
     - yes
     - yes
     - yes
     - yes
   * - nose2
     - yes
     - yes
     - yes
     - yes
     - yes
   * - py.test
     - yes
     - yes
     - yes
     - yes
     - yes
   * - | unittest
       | (``@parameterized.expand``)
     - yes
     - yes
     - yes
     - yes
     - yes
   * - | unittest2
       | (``@parameterized.expand``)
     - yes
     - yes
     - yes
     - yes
     - yes

Dependencies
------------

(this section left intentionally blank)


Exhaustive Usage Examples
--------------------------

The ``@parameterized`` and ``@parameterized.expand`` decorators accept a list
or iterable of tuples or ``param(...)``, or a callable which returns a list or
iterable:

.. code:: python

    from parameterized import parameterized, param

    # A list of tuples
    @parameterized([
        (2, 3, 5),
        (3, 5, 8),
    ])
    def test_add(a, b, expected):
        assert_equal(a + b, expected)

    # A list of params
    @parameterized([
        param("10", 10),
        param("10", 16, base=16),
    ])
    def test_int(str_val, expected, base=10):
        assert_equal(int(str_val, base=base), expected)

    # An iterable of params
    @parameterized(
        param.explicit(*json.loads(line))
        for line in open("testcases.jsons")
    )
    def test_from_json_file(...):
        ...

    # A callable which returns a list of tuples
    def load_test_cases():
        return [
            ("test1", ),
            ("test2", ),
        ]
    @parameterized(load_test_cases)
    def test_from_function(name):
        ...

.. **

Note that, when using an iterator or a generator, all the items will be loaded
into memory before the start of the test run (we do this explicitly to ensure
that generators are exhausted exactly once in multi-process or multi-threaded
testing environments).

The ``@parameterized`` decorator can be used test class methods, and standalone
functions:

.. code:: python

    from parameterized import parameterized

    class AddTest(object):
        @parameterized([
            (2, 3, 5),
        ])
        def test_add(self, a, b, expected):
            assert_equal(a + b, expected)

    @parameterized([
        (2, 3, 5),
    ])
    def test_add(a, b, expected):
        assert_equal(a + b, expected)


And ``@parameterized.expand`` can be used to generate test methods in
situations where test generators cannot be used (for example, when the test
class is a subclass of ``unittest.TestCase``):

.. code:: python

    import unittest
    from parameterized import parameterized

    class AddTestCase(unittest.TestCase):
        @parameterized.expand([
            ("2 and 3", 2, 3, 5),
            ("3 and 5", 2, 3, 5),
        ])
        def test_add(self, _, a, b, expected):
            assert_equal(a + b, expected)

Will create the test cases::

    $ nosetests example.py
    test_add_0_2_and_3 (example.AddTestCase) ... ok
    test_add_1_3_and_5 (example.AddTestCase) ... ok

    ----------------------------------------------------------------------
    Ran 2 tests in 0.001s

    OK

Note that ``@parameterized.expand`` works by creating new methods on the test
class. If the first parameter is a string, that string will be added to the end
of the method name. For example, the test case above will generate the methods
``test_add_0_2_and_3`` and ``test_add_1_3_and_5``.

The names of the test cases generated by ``@parameterized.expand`` can be
customized using the ``testcase_func_name`` keyword argument. The value should
be a function which accepts three arguments: ``testcase_func``, ``param_num``,
and ``params``, and it should return the name of the test case.
``testcase_func`` will be the function to be tested, ``param_num`` will be the
index of the test case parameters in the list of parameters, and ``param``
(an instance of ``param``) will be the parameters which will be used.

.. code:: python

    import unittest
    from parameterized import parameterized

    def custom_name_func(testcase_func, param_num, param):
        return "%s_%s" %(
            testcase_func.__name__,
            parameterized.to_safe_name("_".join(str(x) for x in param.args)),
        )

    class AddTestCase(unittest.TestCase):
        @parameterized.expand([
            (2, 3, 5),
            (2, 3, 5),
        ], testcase_func_name=custom_name_func)
        def test_add(self, a, b, expected):
            assert_equal(a + b, expected)

Will create the test cases::

    $ nosetests example.py
    test_add_1_2_3 (example.AddTestCase) ... ok
    test_add_2_3_5 (example.AddTestCase) ... ok

    ----------------------------------------------------------------------
    Ran 2 tests in 0.001s

    OK


The ``param(...)`` helper class stores the parameters for one specific test
case.  It can be used to pass keyword arguments to test cases:

.. code:: python

    from parameterized import parameterized, param

    @parameterized([
        param("10", 10),
        param("10", 16, base=16),
    ])
    def test_int(str_val, expected, base=10):
        assert_equal(int(str_val, base=base), expected)


If test cases have a docstring, the parameters for that test case will be
appended to the first line of the docstring. This behavior can be controlled
with the ``doc_func`` argument:

.. code:: python

    from parameterized import parameterized

    @parameterized([
        (1, 2, 3),
        (4, 5, 9),
    ])
    def test_add(a, b, expected):
        """ Test addition. """
        assert_equal(a + b, expected)

    def my_doc_func(func, num, param):
        return "%s: %s with %s" %(num, func.__name__, param)

    @parameterized([
        (5, 4, 1),
        (9, 6, 3),
    ], doc_func=my_doc_func)
    def test_subtraction(a, b, expected):
        assert_equal(a - b, expected)

::

    $ nosetests example.py
    Test addition. [with a=1, b=2, expected=3] ... ok
    Test addition. [with a=4, b=5, expected=9] ... ok
    0: test_subtraction with param(*(5, 4, 1)) ... ok
    1: test_subtraction with param(*(9, 6, 3)) ... ok

    ----------------------------------------------------------------------
    Ran 4 tests in 0.001s

    OK


Migrating from ``nose-parameterized`` to ``parameterized``
----------------------------------------------------------

To migrate a codebase from ``nose-parameterized`` to ``parameterized``:

1. Update your requirements file, replacing ``nose-parameterized`` with
   ``parameterized``.

2. Replace all references to ``nose_parameterized`` with ``parameterized``::

    $ perl -pi -e 's/nose_parameterized/parameterized/g' your-codebase/

3. You're done!


FAQ
---

What happened to ``nose-parameterized``?
    Originally only nose was supported. But now everything is supported, and it
    only made sense to change the name!

What do you mean when you say "nose is best supported"?
    There are small caveates with ``py.test`` and ``unittest``: ``py.test``
    does not show the parameter values (ex, it will show ``test_add[0]``
    instead of ``test_add[1, 2, 3]``), and ``unittest``/``unittest2`` do not
    support test generators so ``@parameterized.expand`` must be used.

Why not use ``@pytest.mark.parametrize``?
    Because spelling is difficult. Also, ``parameterized`` doesn't require you
    to repeat argument names, and (using ``param``) it supports optional
    keyword arguments.

Why do I get an ``AttributeError: 'function' object has no attribute 'expand'`` with ``@parameterized.expand``?
    You've likely installed the ``parametrized`` (note the missing *e*)
    package. Use ``parameterized`` (with the *e*) instead and you'll be all
    set.
