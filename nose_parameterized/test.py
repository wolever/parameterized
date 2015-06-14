# coding=utf-8

import inspect
from unittest import TestCase
from nose.tools import assert_equal
from nose.plugins.skip import SkipTest

from .parameterized import (
    PY3, parameterized, param, parameterized_argument_value_pairs, short_repr,
)

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
    "test_on_TestCase2_custom_name_42(42, bar=None)",
    "test_on_TestCase2_custom_name_foo0('foo0', bar=None)",
    "test_on_TestCase2_custom_name_foo1('foo1', bar=None)",
    "test_on_TestCase2_custom_name_foo2('foo2', bar=42)",
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


def custom_naming_func(custom_tag):
    def custom_naming_func(testcase_func, param_num, param):
        return testcase_func.__name__ + ('_%s_name_' % custom_tag) + str(param.args[0])

    return custom_naming_func

def custom_doc_func(testcase_func, param_num, param):
    return testcase_func.__doc__ + ' ' + str(param.args[0])


class TestParamerizedOnTestCase(TestCase):
    @parameterized.expand(test_params)
    def test_on_TestCase(self, foo, bar=None):
        missing_tests.remove("test_on_TestCase(%r, bar=%r)" %(foo, bar))

    @parameterized.expand(test_params,
                          testcase_func_name=custom_naming_func("custom"))
    def test_on_TestCase2(self, foo, bar=None):
        stack = inspect.stack()
        frame = stack[1]
        frame_locals = frame[0].f_locals
        nose_test_method_name = frame_locals['a'][0]._testMethodName
        expected_name = "test_on_TestCase2_custom_name_" + str(foo)
        assert_equal(nose_test_method_name, expected_name,
                     "Test Method name '%s' did not get customized to expected: '%s'" %
                     (nose_test_method_name, expected_name))
        missing_tests.remove("%s(%r, bar=%r)" %(expected_name, foo, bar))

class TestParameterizedExpandDocstring(TestCase):

    def _get_test_method_documentation(self):
        """Get test method documentation.

        This function must be called directly by a test method
        in this class, as it uses inspect to walk the call stack to find
        the test methods's documentation.
        """
        stack = inspect.stack()
        frame = stack[2]
        frame_locals = frame[0].f_locals
        return frame_locals['a'][0]._testMethodDoc

    def _assert_documentation_is_equal(self,
                                       actual_test_method_doc,
                                       expected_test_method_doc):
        """Wrapper around assert_equal for test method documentation."""
        assert_equal(actual_test_method_doc,
                     expected_test_method_doc,
                     "Test Method doc '%s' did not get customized to expected: '%s'" %
                     (actual_test_method_doc, expected_test_method_doc))

    @parameterized.expand([param("foo")],
                          testcase_func_doc=custom_doc_func)
    def test_custom_doc_func(self, foo, bar=None):
        """Documentation"""
        expected_doc = "Documentation " + str(foo)
        actual_doc = self._get_test_method_documentation()
        self._assert_documentation_is_equal(actual_doc, expected_doc)

    @parameterized.expand([param("foo")])
    def test_single_line_documentation(self, foo):
        """Documentation."""
        expected_doc = ("Documentation [with foo=%r]." % (foo))
        actual_doc = self._get_test_method_documentation()
        self._assert_documentation_is_equal(actual_doc, expected_doc)

    @parameterized.expand([param("foo")])
    def test_multiline_documentation(self, foo):
        """Documentation.

        More"""
        expected_doc = ("Documentation [with foo=%r].\n\n"
                        "        More" % (foo))
        actual_doc = self._get_test_method_documentation()
        self._assert_documentation_is_equal(actual_doc, expected_doc)

    @parameterized.expand([param("foo")])
    def test_unicode_documentation(self, foo):
        u"""Döcumentation."""
        expected_doc = (u"Döcumentation [with foo=%r]." % (foo))
        actual_doc = self._get_test_method_documentation()
        self._assert_documentation_is_equal(actual_doc, expected_doc)

    @parameterized.expand([param("foo", )])
    def test_default_values_get_correct_value(self, foo, bar=12):
        """Documentation"""
        expected_doc = "Documentation [with foo=%r, bar=%r]" % (foo, bar)
        actual_doc = self._get_test_method_documentation()
        self._assert_documentation_is_equal(actual_doc, expected_doc)

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
    if PY3:
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


@parameterized([
    ("foo", param(1), [("foo", 1)]),
    ("foo, *a", param(1), [("foo", 1)]),
    ("foo, *a", param(1, 9), [("foo", 1), ("*a", (9, ))]),
    ("foo, *a, **kw", param(1, bar=9), [("foo", 1), ("**kw", {"bar": 9})]),
    ("x=9", param(), [("x", 9)]),
    ("x=9", param(1), [("x", 1)]),
    ("x, y=9, *a, **kw", param(1), [("x", 1), ("y", 9)]),
    ("x, y=9, *a, **kw", param(1, 2), [("x", 1), ("y", 2)]),
    ("x, y=9, *a, **kw", param(1, 2, 3), [("x", 1), ("y", 2), ("*a", (3, ))]),
    ("x, y=9, *a, **kw", param(1, y=2), [("x", 1), ("y", 2)]),
    ("x, y=9, *a, **kw", param(1, z=2), [("x", 1), ("y", 9), ("**kw", {"z": 2})]),
    ("x, y=9, *a, **kw", param(1, 2, 3, z=3), [("x", 1), ("y", 2), ("*a", (3, )), ("**kw", {"z": 3})]),
])
def test_parameterized_argument_value_pairs(func_params, p, expected):
    helper = eval("lambda %s: None" %(func_params, ))
    actual = parameterized_argument_value_pairs(helper, p)
    assert_equal(actual, expected)


@parameterized([
    ("abcd", "'abcd'"),
    ("123456789", "'12...89'"),
    (123456789, "123...789")  # number types do not have quotes, so we can repr more
])
def test_short_repr(input, expected, n=6):
    assert_equal(short_repr(input, n=n), expected)
