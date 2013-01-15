``nose-patameterized`` is a decorator for parameterized testing with ``nose``
=============================================================================

Nose. It's got test generators. But they kind of suck, because:

    * They often require a second function
    * They make it difficult to separate the data from the test
    * They don't work with subclases of ``unittest.TestCase``

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
            (-1.5, -2.0),
            (1.0, 1.0),
            (1.6, 1),
        ])
        def test_floor(self, input, expected):
            assert_equal(math.floor(input), expected)
    $ nosetests -v test_math.py
    test_math.test_pow(2, 2, 4) ... ok
    test_math.test_pow(2, 3, 8) ... ok
    test_math.test_pow(1, 9, 1) ... ok
    test_math.test_pow(0, 9, 0) ... ok
    test_floor_0 (test_math.TestMathUnitTest) ... ok
    test_floor_1 (test_math.TestMathUnitTest) ... ok
    test_floor_2 (test_math.TestMathUnitTest) ... ok

    ----------------------------------------------------------------------
    Ran 7 tests in 0.002s

    OK

**Now with Python 3 support!**
