``nose-parameterized`` is a decorator for parameterized testing with ``nose``
=============================================================================

*Now with 100% less Python 3 incompatibility!*

Nose. It's got test generators. But they kind of suck:

    * They often require a second function
    * They make it difficult to separate the data from the test
    * They don't work with subclases of ``unittest.TestCase``
    * ``kwargs``? What ``kwargs``?

But ``nose-parameterized`` fixes that::

    $ cat test_math.py
    from nose.tools import assert_equal
    from nose_parameterized import parameterized

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
        def test_floor(self, input, expected):
            assert_equal(math.floor(input), expected)

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


Exhaustive Usage Examples
--------------------------

The ``@parameterized`` and ``@parameterized.expected`` decorators accept a list
or iterable of tuples or ``param(...)``, or a callable which returns a list or
iterable::

    from nose_parameterized import parameterized, param

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


Note that, when using an iterator or a generator, Nose will read every item
into memory before running any tests (as it first finds and loads every test in
each test file, then executes all of them at once).

The ``@parameterized`` decorator can be used test class methods, and standalone
functions::

    from nose_parameterized import parameterized

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
sitautions where test generators cannot be used (for example, when the test
class is a subclass of ``unittest.TestCase``)::

    import unittest
    from nose_parameterized import parameterized

    class AddTestCase(unittest.TestCase):
        @parameterized.expand([
            ("2 and 3", 2, 3, 5),
            ("3 and 5", 2, 3, 5),
        ])
        def test_add(self, _, a, b, expected):
            assert_equal(a + b, expected)


Note that ``@parameterized.expand`` works by creating new methods on the test
class. If the first parameter is a string, that string will be added to the end
of the method name. For example, the test case above will generate the methods
``test_add_0_2_and_3`` and ``test_add_1_3_and_5``.

The ``param(...)`` helper represents the parameters for one specific test case.
It can be used to pass keyword arguments to test cases::

    from nose_parameterized import parameterized, param

    @parameterized([
        param("10", 10),
        param("10", 16, base=16),
    ])
    def test_int(str_val, expected, base=10):
        assert_equal(int(str_val, base=base), expected)
