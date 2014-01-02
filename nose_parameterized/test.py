from unittest import TestCase
from nose.tools import assert_equal
from nose.plugins.skip import SkipTest

from . import six
from .parameterized import parameterized, param

def assert_contains(haystack, needle):
    if needle not in haystack:
        raise AssertionError("%r not in %r" %(needle, haystack))

missing_tests = set([
    "test_naked_function(42, bar=None)",
    "test_naked_function('foo0', bar=None)",
    "test_naked_function('foo1', bar=None)",
    "test_naked_function('foo2', bar=42)",
    "test_instance_method(42, bar=None)",
    "test_instance_method('foo0', bar=None)",
    "test_instance_method('foo1', bar=None)",
    "test_instance_method('foo2', bar=42)",
    "test_on_TestCase(42, bar=None)",
    "test_on_TestCase('foo0', bar=None)",
    "test_on_TestCase('foo1', bar=None)",
    "test_on_TestCase('foo2', bar=42)",
    "test_on_old_style_class('foo')",
    "test_on_old_style_class('bar')",
])

test_params = [
    (42, ),
    "foo0",
    param("foo1"),
    param("foo2", bar=42),
]

@parameterized(test_params)
def test_naked_function(foo, bar=None):
    missing_tests.remove("test_naked_function(%r, bar=%r)" %(foo, bar))


class TestParameterized(object):
    @parameterized(test_params)
    def test_instance_method(self, foo, bar=None):
        missing_tests.remove("test_instance_method(%r, bar=%r)" %(foo, bar))


class TestParamerizedOnTestCase(TestCase):
    @parameterized.expand(test_params)
    def test_on_TestCase(self, foo, bar=None):
        missing_tests.remove("test_on_TestCase(%r, bar=%r)" %(foo, bar))


def test_warns_when_using_parameterized_with_TestCase():
    try:
        class TestTestCaseWarnsOnBadUseOfParameterized(TestCase):
            @parameterized([42])
            def test_in_subclass_of_TestCase(self, foo):
                pass
    except Exception as e:
        assert_contains(str(e), "parameterized.expand")
    else:
        raise AssertionError("Expected exception not raised")

missing_tests.add("test_wrapped_iterable_input()")
@parameterized(lambda: iter(["foo"]))
def test_wrapped_iterable_input(foo):
    missing_tests.remove("test_wrapped_iterable_input()")

def test_helpful_error_on_non_iterable_input():
    try:
        for _ in parameterized(lambda: 42)(lambda: None)():
            pass
    except Exception as e:
        assert_contains(str(e), "expected iterable input")
    else:
        raise AssertionError("Expected exception not raised")


def teardown_module():
    missing = sorted(list(missing_tests))
    assert_equal(missing, [])


def test_old_style_classes():
    if six.PY3:
        raise SkipTest("Py3 doesn't have old-style classes")
    class OldStyleClass:
        @parameterized(["foo"])
        def parameterized_method(self, param):
            pass
    try:
        list(OldStyleClass().parameterized_method())
    except TypeError as e:
        assert_contains(str(e), "new-style")
        assert_contains(str(e), "parameterized.expand")
        assert_contains(str(e), "OldStyleClass")
    else:
        raise AssertionError("expected TypeError not raised by old-style class")


class TestOldStyleClass:
    @parameterized.expand(["foo", "bar"])
    def test_old_style_classes(self, param):
        missing_tests.remove("test_on_old_style_class(%r)" %(param, ))
