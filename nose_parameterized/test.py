# coding=utf-8

import inspect
from unittest import TestCase
from nose.tools import assert_equal
from nose.plugins.skip import SkipTest

from .parameterized import (
    PY3, PY2, parameterized, param, parameterized_argument_value_pairs,
    short_repr,
)

def assert_contains(haystack, needle):
    if needle not in haystack:
        raise AssertionError("%r not in %r" %(needle, haystack))

def detect_runner(candidates):
    for x in reversed(inspect.stack()):
        frame = x[0]
        for mod in candidates:
            frame_mod = frame.f_globals.get("__name__", "")
            if frame_mod == mod or frame_mod.startswith(mod + "."):
                return mod
    return "<unknown>"

runner = detect_runner(["nose", "nose2","unittest", "unittest2"])
UNITTEST = runner.startswith("unittest")
NOSE2 = (runner == "nose2")

SKIP_FLAGS = {
    "generator": UNITTEST,
    # nose2 doesn't run tests on old-style classes under Py2, so don't expect
    # these tests to run under nose2.
    "py2nose2": (PY2 and NOSE2),
}

missing_tests = set()

def expect(skip, tests=None):
    if tests is None:
        tests = skip
        skip = None
    if any(SKIP_FLAGS.get(f) for f in (skip or "").split()):
        return
    missing_tests.update(tests)


if not (PY2 and NOSE2):
    missing_tests.update([
    ])

test_params = [
    (42, ),
    "foo0",
    param("foo1"),
    param("foo2", bar=42),
]

expect("generator", [
    "test_naked_function('foo0', bar=None)",
    "test_naked_function('foo1', bar=None)",
    "test_naked_function('foo2', bar=42)",
    "test_naked_function(42, bar=None)",
])

@parameterized(test_params)
def test_naked_function(foo, bar=None):
    missing_tests.remove("test_naked_function(%r, bar=%r)" %(foo, bar))


class TestParameterized(object):
    expect("generator", [
        "test_instance_method('foo0', bar=None)",
        "test_instance_method('foo1', bar=None)",
        "test_instance_method('foo2', bar=42)",
        "test_instance_method(42, bar=None)",
    ])

    @parameterized(test_params)
    def test_instance_method(self, foo, bar=None):
        missing_tests.remove("test_instance_method(%r, bar=%r)" %(foo, bar))


def custom_naming_func(custom_tag):
    def custom_naming_func(testcase_func, param_num, param):
        return testcase_func.__name__ + ('_%s_name_' % custom_tag) + str(param.args[0])

    return custom_naming_func


class TestParamerizedOnTestCase(TestCase):
    expect([
        "test_on_TestCase('foo0', bar=None)",
        "test_on_TestCase('foo1', bar=None)",
        "test_on_TestCase('foo2', bar=42)",
        "test_on_TestCase(42, bar=None)",
    ])

    @parameterized.expand(test_params)
    def test_on_TestCase(self, foo, bar=None):
        missing_tests.remove("test_on_TestCase(%r, bar=%r)" %(foo, bar))

    expect([
        "test_on_TestCase2_custom_name_42(42, bar=None)",
        "test_on_TestCase2_custom_name_foo0('foo0', bar=None)",
        "test_on_TestCase2_custom_name_foo1('foo1', bar=None)",
        "test_on_TestCase2_custom_name_foo2('foo2', bar=42)",
    ])

    @parameterized.expand(test_params,
                          name_func=custom_naming_func("custom"))
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
    def _assert_docstring(self, expected_docstring, rstrip=False):
        """ Checks the current test method's docstring. Must be called directly
            from the test method. """
        stack = inspect.stack()
        f_locals = stack[3][0].f_locals
        test_method = (
            f_locals.get("testMethod") or # Py27
            f_locals.get("function") # Py33
        )
        if test_method is None:
            raise AssertionError("uh oh, unittest changed a local variable name")
        actual_docstring = test_method.__doc__
        if rstrip:
            actual_docstring = actual_docstring.rstrip()
        assert_equal(actual_docstring, expected_docstring)

    @parameterized.expand([param("foo")],
                          doc_func=lambda f, n, p: "stuff")
    def test_custom_doc_func(self, foo, bar=None):
        """Documentation"""
        self._assert_docstring("stuff")

    @parameterized.expand([param("foo")])
    def test_single_line_docstring(self, foo):
        """Documentation."""
        self._assert_docstring("Documentation [with foo=%r]." %(foo, ))

    @parameterized.expand([param("foo")])
    def test_empty_docstring(self, foo):
        ""
        self._assert_docstring("[with foo=%r]" %(foo, ))

    @parameterized.expand([param("foo")])
    def test_multiline_documentation(self, foo):
        """Documentation.

        More"""
        self._assert_docstring(
            "Documentation [with foo=%r].\n\n"
            "        More" %(foo, )
        )

    @parameterized.expand([param("foo")])
    def test_unicode_docstring(self, foo):
        u"""Döcumentation."""
        self._assert_docstring(u"Döcumentation [with foo=%r]." %(foo, ))

    @parameterized.expand([param("foo", )])
    def test_default_values_get_correct_value(self, foo, bar=12):
        """Documentation"""
        self._assert_docstring("Documentation [with foo=%r, bar=%r]" %(foo, bar))

    @parameterized.expand([param("foo", )])
    def test_with_leading_newline(self, foo, bar=12):
        """
        Documentation
        """
        self._assert_docstring("Documentation [with foo=%r, bar=%r]" %(foo, bar), rstrip=True)


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

expect("generator", [
    "test_wrapped_iterable_input('foo')",
])
@parameterized(lambda: iter(["foo"]))
def test_wrapped_iterable_input(foo):
    missing_tests.remove("test_wrapped_iterable_input(%r)" %(foo, ))

def test_helpful_error_on_non_iterable_input():
    try:
        for _ in parameterized(lambda: 42)(lambda: None)():
            pass
    except Exception as e:
        assert_contains(str(e), "is not iterable")
    else:
        raise AssertionError("Expected exception not raised")


def tearDownModule():
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
    expect("py2nose2 generator", [
        "test_on_old_style_class('foo')",
        "test_on_old_style_class('bar')",
    ])

    @parameterized.expand(["foo", "bar"])
    def test_old_style_classes(self, param):
        missing_tests.remove("test_on_old_style_class(%r)" %(param, ))


@parameterized([
    ("", param(), []),
    ("*a, **kw", param(), []),
    ("*a, **kw", param(1, foo=42), [("*a", (1, )), ("**kw", {"foo": 42})]),
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

@parameterized([
    ("foo", ),
])
def test_with_docstring(input):
    """ Docstring! """
    pass
