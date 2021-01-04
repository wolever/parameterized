# coding=utf-8

import inspect
import mock
from unittest import TestCase
from nose.tools import assert_equal, assert_raises

from .parameterized import (
    PY3, PY2, parameterized, param, parameterized_argument_value_pairs,
    short_repr, detect_runner, parameterized_class, SkipTest,
)

def assert_contains(haystack, needle):
    if needle not in haystack:
        raise AssertionError("%r not in %r" %(needle, haystack))

runner = detect_runner()
UNITTEST = runner.startswith("unittest")
NOSE2 = (runner == "nose2")
PYTEST = (runner == "pytest")

SKIP_FLAGS = {
    "generator": UNITTEST,
    "standalone": UNITTEST,
    # nose2 doesn't run tests on old-style classes under Py2, so don't expect
    # these tests to run under nose2.
    "py2nose2": (PY2 and NOSE2),
    "pytest": PYTEST,
}

missing_tests = set()

def expect(skip, tests=None):
    if tests is None:
        tests = skip
        skip = None
    if any(SKIP_FLAGS.get(f) for f in (skip or "").split()):
        return
    missing_tests.update(tests)

test_params = [
    (42, ),
    "foo0",
    param("foo1"),
    param("foo2", bar=42),
]

expect("standalone", [
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


if not PYTEST:
    # py.test doesn't use xunit-style setup/teardown, so these tests don't apply
    class TestSetupTeardown(object):
        expect("generator", [
            "test_setup(setup 1)",
            "teardown_called(teardown 1)",
            "test_setup(setup 2)",
            "teardown_called(teardown 2)",
        ])

        stack = ["setup 1", "teardown 1", "setup 2", "teardown 2"]
        actual_order = "error: setup not called"

        def setUp(self):
            self.actual_order = self.stack.pop(0)

        def tearDown(self):
            missing_tests.remove("teardown_called(%s)" %(self.stack.pop(0), ))

        @parameterized([(1, ), (2, )])
        def test_setup(self, count, *a):
            assert_equal(self.actual_order, "setup %s" %(count, ))
            missing_tests.remove("test_setup(%s)" %(self.actual_order, ))


def custom_naming_func(custom_tag):
    def custom_naming_func(testcase_func, param_num, param):
        return testcase_func.__name__ + ('_%s_name_' % custom_tag) + str(param.args[0])

    return custom_naming_func


@mock.patch("os.getpid")
class TestParameterizedExpandWithMockPatchForClass(TestCase):
    expect([
        "test_one_function_patch_decorator('foo1', 'umask', 'getpid')",
        "test_one_function_patch_decorator('foo0', 'umask', 'getpid')",
        "test_one_function_patch_decorator(42, 'umask', 'getpid')",
    ])

    @parameterized.expand([(42, ), "foo0", param("foo1")])
    @mock.patch("os.umask")
    def test_one_function_patch_decorator(self, foo, mock_umask, mock_getpid):
        missing_tests.remove("test_one_function_patch_decorator(%r, %r, %r)" %
                             (foo, mock_umask._mock_name,
                              mock_getpid._mock_name))

    expect([
        "test_multiple_function_patch_decorator"
        "(42, 51, 'umask', 'fdopen', 'getpid')",
        "test_multiple_function_patch_decorator"
        "('foo0', 'bar0', 'umask', 'fdopen', 'getpid')",
        "test_multiple_function_patch_decorator"
        "('foo1', 'bar1', 'umask', 'fdopen', 'getpid')",
    ])

    @parameterized.expand([(42, 51), ("foo0", "bar0"), param("foo1", "bar1")])
    @mock.patch("os.fdopen")
    @mock.patch("os.umask")
    def test_multiple_function_patch_decorator(self, foo, bar, mock_umask,
                                               mock_fdopen, mock_getpid):
        missing_tests.remove("test_multiple_function_patch_decorator"
                             "(%r, %r, %r, %r, %r)" %
                             (foo, bar, mock_umask._mock_name,
                              mock_fdopen._mock_name, mock_getpid._mock_name))


@mock.patch("os.getpid")
class TestParameterizedExpandWithNoExpand(object):
    expect("generator", [
        "test_patch_class_no_expand(42, 51, 'umask', 'getpid')",
    ])

    @parameterized([(42, 51)])
    @mock.patch("os.umask")
    def test_patch_class_no_expand(self, foo, bar, mock_umask, mock_getpid):
        missing_tests.remove("test_patch_class_no_expand"
                             "(%r, %r, %r, %r)" %
                             (foo, bar, mock_umask._mock_name,
                              mock_getpid._mock_name))


class TestParameterizedExpandWithNoMockPatchForClass(TestCase):
    expect([
        "test_one_function_patch_decorator('foo1', 'umask')",
        "test_one_function_patch_decorator('foo0', 'umask')",
        "test_one_function_patch_decorator(42, 'umask')",
    ])

    @parameterized.expand([(42, ), "foo0", param("foo1")])
    @mock.patch("os.umask")
    def test_one_function_patch_decorator(self, foo, mock_umask):
        missing_tests.remove("test_one_function_patch_decorator(%r, %r)" %
                             (foo, mock_umask._mock_name))

    expect([
        "test_multiple_function_patch_decorator(42, 51, 'umask', 'fdopen')",
        "test_multiple_function_patch_decorator('foo0', 'bar0', 'umask', 'fdopen')",
        "test_multiple_function_patch_decorator('foo1', 'bar1', 'umask', 'fdopen')",
    ])

    @parameterized.expand([(42, 51), ("foo0", "bar0"), param("foo1", "bar1")])
    @mock.patch("os.fdopen")
    @mock.patch("os.umask")
    def test_multiple_function_patch_decorator(self, foo, bar, mock_umask,
                                               mock_fdopen):
        missing_tests.remove("test_multiple_function_patch_decorator"
                             "(%r, %r, %r, %r)" %
                             (foo, bar, mock_umask._mock_name,
                              mock_fdopen._mock_name))


class TestParameterizedExpandWithNoMockPatchForClassNoExpand(object):
    expect("generator", [
        "test_patch_no_expand(42, 51, 'umask')",
    ])

    @parameterized([(42, 51)])
    @mock.patch("os.umask")
    def test_patch_no_expand(self, foo, bar, mock_umask):
        missing_tests.remove("test_patch_no_expand(%r, %r, %r)" %
                             (foo, bar, mock_umask._mock_name))


expect("standalone", [
    "test_mock_patch_standalone_function(42, 'umask')",
])

@parameterized([(42, )])
@mock.patch("os.umask")
def test_mock_patch_standalone_function(foo, mock_umask):
    missing_tests.remove(
        "test_mock_patch_standalone_function(%r, %r)" %(
            foo, mock_umask._mock_name
        )
    )


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
            f_locals.get("function") or # Py33
            f_locals.get("method") or # Py38
            f_locals.get("testfunction") or # Py382
            None
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
            @parameterized([(42, )])
            def test_in_subclass_of_TestCase(self, foo):
                pass
    except Exception as e:
        assert_contains(str(e), "parameterized.expand")
    else:
        raise AssertionError("Expected exception not raised")

def test_helpful_error_on_invalid_parameters():
    try:
        parameterized([1432141234243])(lambda: None)
    except Exception as e:
        assert_contains(str(e), "Parameters must be tuples")
    else:
        raise AssertionError("Expected exception not raised")


def test_helpful_error_on_empty_iterable_input():
    try:
        parameterized([])(lambda: None)
    except ValueError as e:
        assert_contains(str(e), "iterable is empty")
    else:
        raise AssertionError("Expected exception not raised")

def test_skip_test_on_empty_iterable():
    func = parameterized([], skip_on_empty=True)(lambda: None)
    assert_raises(SkipTest, func)


def test_helpful_error_on_empty_iterable_input_expand():
    try:
        class ExpectErrorOnEmptyInput(TestCase):
            @parameterized.expand([])
            def test_expect_error(self):
                pass
    except ValueError as e:
        assert_contains(str(e), "iterable is empty")
    else:
        raise AssertionError("Expected exception not raised")


expect("stadalone generator", [
    "test_wrapped_iterable_input('foo')",
])
@parameterized(lambda: iter(["foo"]))
def test_wrapped_iterable_input(foo):
    missing_tests.remove("test_wrapped_iterable_input(%r)" %(foo, ))

def test_helpful_error_on_non_iterable_input():
    try:
        parameterized(lambda: 42)(lambda: None)
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
    (123456789, "123...789"),
    (123456789, "12...89", 4),
])
def test_short_repr(input, expected, n=6):
    assert_equal(short_repr(input, n=n), expected)

@parameterized([
    ("foo", ),
])
def test_with_docstring(input):
    """ Docstring! """
    pass


cases_over_10 = [(i, i+1) for i in range(11)]

@parameterized(cases_over_10)
def test_cases_over_10(input, expected):
    assert_equal(input, expected-1)


@parameterized_class(("a", "b", "c"), [
    ("foo", 1, 2),
    (0, 1, 2),
])
class TestParameterizedClass(TestCase):
    expect([
        "TestParameterizedClass_0_foo:test_method_a('foo', 1, 2)",
        "TestParameterizedClass_0_foo:test_method_b('foo', 1, 2)",
        "TestParameterizedClass_0_foo:testCamelCaseMethodC('foo', 1, 2)",
        "TestParameterizedClass_1:test_method_a(0, 1, 2)",
        "TestParameterizedClass_1:test_method_b(0, 1, 2)",
        "TestParameterizedClass_1:testCamelCaseMethodC(0, 1, 2)",
    ])

    def _assertions(self, test_name):
        assert hasattr(self, "a")
        assert_equal(self.b + self.c, 3)
        missing_tests.remove("%s:%s(%r, %r, %r)" %(
            self.__class__.__name__,
            test_name,
            self.a,
            self.b,
            self.c,
        ))

    def test_method_a(self):
        self._assertions("test_method_a")

    def test_method_b(self):
        self._assertions("test_method_b")

    def testCamelCaseMethodC(self):
        self._assertions("testCamelCaseMethodC")


@parameterized_class(("a", ), [
    (1, ),
    (2, ),
], class_name_func=lambda cls, idx, attrs: "%s_custom_func_%s" %(cls.__name__, attrs["a"]))
class TestNamedParameterizedClass(TestCase):
    expect([
        "TestNamedParameterizedClass_custom_func_1:test_method(1)",
        "TestNamedParameterizedClass_custom_func_2:test_method(2)",
    ])

    def test_method(self):
        missing_tests.remove("%s:test_method(%r)" %(
            self.__class__.__name__,
            self.a,
        ))


@parameterized_class([
    {"foo": 42},
    {"bar": "some stuff"},
    {"bar": "other stuff", "name": "some name", "foo": 12},
])
class TestParameterizedClassDict(TestCase):
    expect([
        "TestParameterizedClassDict_0:setUp(42, 'empty')",
        "TestParameterizedClassDict_0:test_method(42, 'empty')",
        "TestParameterizedClassDict_0:tearDown(42, 'empty')",
        "TestParameterizedClassDict_1_some_stuff:setUp(0, 'some stuff')",
        "TestParameterizedClassDict_1_some_stuff:test_method(0, 'some stuff')",
        "TestParameterizedClassDict_1_some_stuff:tearDown(0, 'some stuff')",
        "TestParameterizedClassDict_2_some_name:setUp(12, 'other stuff')",
        "TestParameterizedClassDict_2_some_name:test_method(12, 'other stuff')",
        "TestParameterizedClassDict_2_some_name:tearDown(12, 'other stuff')",
    ])

    foo = 0
    bar = 'empty'

    def setUp(self):
        # Ensure that super() works (issue #73)
        super(TestParameterizedClassDict, self).setUp()
        missing_tests.remove("%s:setUp(%r, %r)" %(
            self.__class__.__name__,
            self.foo,
            self.bar,
        ))

    def tearDown(self):
        # Ensure that super() works (issue #73)
        super(TestParameterizedClassDict, self).tearDown()
        missing_tests.remove("%s:tearDown(%r, %r)" %(
            self.__class__.__name__,
            self.foo,
            self.bar,
        ))

    def test_method(self):
        missing_tests.remove("%s:test_method(%r, %r)" %(
            self.__class__.__name__,
            self.foo,
            self.bar,
        ))


class TestUnicodeDocstring(object):
    @parameterized.expand([
        'value1',
        'vålüé¡'
    ])
    def test_with_docstring(self, param):
        """ Это док-стринг, содержащий не-ascii символы """
        pass
