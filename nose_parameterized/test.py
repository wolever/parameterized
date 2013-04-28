from unittest import TestCase

from nose.tools import assert_equal

from .parameterized import parameterized

def assert_contains(haystack, needle):
    if needle not in haystack:
        raise AssertionError("%r not in %r" %(needle, haystack))

missing_tests = set([
    "test_parameterized_naked_function",
    "test_parameterized_instance_method",
    "test_parameterized_on_TestCase",
])

csv_data = set([
    "run1arg1",
    "run1arg2",
    "run2arg1",
    "run2arg2"
])

@parameterized.from_csv("data.csv")
def test_parameterized_naked_function_from_csv(foo, bar):
    csv_data.remove(foo)
    csv_data.remove(bar)

@parameterized([(42, )])
def test_parameterized_naked_function(foo):
    missing_tests.remove("test_parameterized_naked_function")

class TestParameterized(object):
    @parameterized([(42, )])
    def test_parameterized_instance_method(self, foo):
        missing_tests.remove("test_parameterized_instance_method")

def test_warns_on_bad_use_of_parameterized():
    try:
        class TestTestCaseWarnsOnBadUseOfParameterized(TestCase):
            @parameterized([42])
            def test_should_throw_error(self, param):
                pass
    except Exception as e:
        assert_contains(str(e), "parameterized.expand")
    else:
        raise AssertionError("Expected exception not raised")


class TestParamerizedOnTestCase(TestCase):
    @parameterized.expand([("stuff", )])
    def test_parameterized_on_TestCase(self, input):
        assert_equal(input, "stuff")
        missing_tests.remove("test_parameterized_on_TestCase")
