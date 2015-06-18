import re
import sys
import inspect
from functools import wraps
from collections import namedtuple

try:
    from collections import OrderedDict as MaybeOrderedDict
except ImportError:
    MaybeOrderedDict = dict

from nose.tools import nottest
from unittest import TestCase

PY3 = sys.version_info[0] == 3

if PY3:
    def new_instancemethod(f, *args):
        return f

    # Python 3 doesn't have an InstanceType, so just use a dummy type.
    class InstanceType():
        pass
    lzip = lambda *a: list(zip(*a))
    text_type = str
    string_types = str,
    bytes_type = bytes
else:
    import new
    new_instancemethod = new.instancemethod
    from types import InstanceType
    lzip = zip
    text_type = unicode
    bytes_type = str
    string_types = basestring,

_param = namedtuple("param", "args kwargs")

class param(_param):
    """ Represents a single parameter to a test case.

        For example::

            >>> p = param("foo", bar=16)
            >>> p
            param("foo", bar=16)
            >>> p.args
            ('foo', )
            >>> p.kwargs
            {'bar': 16}

        Intended to be used as an argument to ``@parameterized``::

            @parameterized([
                param("foo", bar=16),
            ])
            def test_stuff(foo, bar=16):
                pass
        """

    def __new__(cls, *args , **kwargs):
        return _param.__new__(cls, args, kwargs)

    @classmethod
    def explicit(cls, args=None, kwargs=None):
        """ Creates a ``param`` by explicitly specifying ``args`` and
            ``kwargs``::

                >>> param.explicit([1,2,3])
                param(*(1, 2, 3))
                >>> param.explicit(kwargs={"foo": 42})
                param(*(), **{"foo": "42"})
            """
        args = args or ()
        kwargs = kwargs or {}
        return cls(*args, **kwargs)

    @classmethod
    def from_decorator(cls, args):
        """ Returns an instance of ``param()`` for ``@parameterized`` argument
            ``args``::

                >>> param.from_decorator((42, ))
                param(args=(42, ), kwargs={})
                >>> param.from_decorator("foo")
                param(args=("foo", ), kwargs={})
            """
        if isinstance(args, param):
            return args
        if isinstance(args, string_types):
            args = (args, )
        return cls(*args)

    def __repr__(self):
        return "param(*%r, **%r)" %self


class QuietOrderedDict(MaybeOrderedDict):
    """ When OrderedDict is available, use it to make sure that the kwargs in
        doc strings are consistently ordered. """
    __str__ = dict.__str__
    __repr__ = dict.__repr__


def parameterized_argument_value_pairs(func, p):
    """Return tuples of parameterized arguments and their values.

        This is useful if you are writing your own testcase_func_doc
        function and need to know the values for each parameter name::

            >>> def func(a, foo=None, bar=42, **kwargs): pass
            >>> p = param(1, foo=7, extra=99)
            >>> parameterized_argument_value_pairs(func, p)
            [("a", 1), ("foo", 7), ("bar", 42), ("**kwargs", {"extra": 99})]

        If the function's first argument is named ``self`` then it will be
        ignored::

            >>> def func(self, a): pass
            >>> p = param(1)
            >>> parameterized_argument_value_pairs(func, p)
            [("a", 1)]

        Additionally, empty ``*args`` or ``**kwargs`` will be ignored::

            >>> def func(foo, *args): pass
            >>> p = param(1)
            >>> parameterized_argument_value_pairs(func, p)
            [("foo", 1)]
            >>> p = param(1, 16)
            >>> parameterized_argument_value_pairs(func, p)
            [("foo", 1), ("*args", (16, ))]
    """
    argspec = inspect.getargspec(func)
    # It may seem to you that @parameterized.expand will never be
    # applied to functions with no arguments so checking that
    # argspec.args is non-empty is unnecessary, but consider this:
    #
    #     @parameterized.expand(...)
    #     @some_other_decorator()
    #     def test_whatever(self, ...)
    #
    # The wider implication of this is that
    # `parameterized_argument_value_pairs` actually doesn't work as
    # intended when @parameterized.expand precedes another decorator
    # rather than being directly attached to the test function it's
    # expanding, but I'm not at all certain what if anything should be
    # done about that, and at least checking if argspec.args is
    # non-empty before trying to dereference it, returns us to the
    # status quo ante, i.e., makes test cases that worked in 0.3.5
    # continue to work in 0.4.x.
    arg_offset = 1 if argspec.args and argspec.args[0] == "self" else 0

    named_args = argspec.args[arg_offset:]

    result = lzip(named_args, p.args)
    named_args = argspec.args[len(result) + arg_offset:]
    varargs = p.args[len(result):]

    result.extend([
        (name, p.kwargs.get(name, default))
        for (name, default)
        in zip(named_args, argspec.defaults or [])
    ])

    seen_arg_names = set([ n for (n, _) in result ])
    keywords = QuietOrderedDict(sorted([
        (name, p.kwargs[name])
        for name in p.kwargs
        if name not in seen_arg_names
    ]))

    if varargs:
        result.append(("*%s" %(argspec.varargs, ), tuple(varargs)))

    if keywords:
        result.append(("**%s" %(argspec.keywords, ), keywords))

    return result

def short_repr(x, n=64):
    """ A shortened repr of ``x`` which is guaranteed to be ``unicode``::

            >>> short_repr("foo")
            u"foo"
            >>> short_repr("123456789", n=4)
            u"12...89"
    """

    x_repr = repr(x)
    if isinstance(x_repr, bytes_type):
        try:
            x_repr = text_type(x_repr, "utf-8")
        except UnicodeDecodeError:
            x_repr = text_type(x_repr, "latin1")
    if len(x_repr) > n:
        x_repr = x_repr[:n//2] + "..." + x_repr[len(x_repr) - n//2:]
    return x_repr

def default_testcase_func_doc(func, num, p):
    if func.__doc__ is None:
        return None

    all_args_with_values = parameterized_argument_value_pairs(func, p)

    # Assumes that the function passed is a bound method.
    descs = ["%s=%s" %(n, short_repr(v)) for n, v in all_args_with_values]

    # The documentation might be a multiline string, so split it
    # and just work with the first string, ignoring the period
    # at the end if there is one.
    first, nl, rest = func.__doc__.partition("\n")
    suffix = ""
    if first.endswith("."):
        suffix = "."
        first = first[:-1]
    args = "%s[with %s]" %(len(first) and " " or "", ", ".join(descs))
    return "".join([first, args, suffix, nl, rest])

class parameterized(object):
    """ Parameterize a test case::

            class TestInt(object):
                @parameterized([
                    ("A", 10),
                    ("F", 15),
                    param("10", 42, base=42)
                ])
                def test_int(self, input, expected, base=16):
                    actual = int(input, base=base)
                    assert_equal(actual, expected)

            @parameterized([
                (2, 3, 5)
                (3, 5, 8),
            ])
            def test_add(a, b, expected):
                assert_equal(a + b, expected)
        """

    def __init__(self, input):
        self.get_input = self.input_as_callable(input)

    def __call__(self, test_func):
        self.assert_not_in_testcase_subclass()

        @wraps(test_func)
        def parameterized_helper_method(test_self=None):
            f = test_func
            if test_self is not None:
                # If we are a test method (which we suppose to be true if we
                # are being passed a "self" argument), we first need to create
                # an instance method, attach it to the instance of the test
                # class, then pull it back off to turn it into a bound method.
                # If we don't do this, Nose gets cranky.
                f = self.make_bound_method(test_self, test_func)
            # Note: because nose is so very picky, the more obvious
            # ``return self.yield_nose_tuples(f)`` won't work here.
            for nose_tuple in self.yield_nose_tuples(f):
                yield nose_tuple

        test_func.__name__ = "_helper_for_%s" %(test_func.__name__, )
        parameterized_helper_method.parameterized_input = input
        parameterized_helper_method.parameterized_func = test_func
        return parameterized_helper_method

    def yield_nose_tuples(self, func):
        for args in self.get_input():
            p = param.from_decorator(args)
            # ... then yield that as a tuple. If those steps aren't
            # followed precicely, Nose gets upset and doesn't run the test
            # or doesn't run setup methods.
            yield self.param_as_nose_tuple(p, func)

    def param_as_nose_tuple(self, p, func):
        nose_func = func
        nose_args = p.args
        if p.kwargs:
            nose_func = wraps(func)(lambda args, kwargs: func(*args, **kwargs))
            nose_args = (p.args, p.kwargs)
        return (nose_func, ) + nose_args

    def make_bound_method(self, instance, func):
        cls = type(instance)
        if issubclass(cls, InstanceType):
            raise TypeError((
                "@parameterized can't be used with old-style classes, but "
                "%r has an old-style class. Consider using a new-style "
                "class, or '@parameterized.expand' "
                "(see http://stackoverflow.com/q/54867/71522 for more "
                "information on old-style classes)."
            ) %(instance, ))
        im_f = new_instancemethod(func, None, cls)
        setattr(cls, func.__name__, im_f)
        return getattr(instance, func.__name__)

    def assert_not_in_testcase_subclass(self):
        parent_classes = self._terrible_magic_get_defining_classes()
        if any(issubclass(cls, TestCase) for cls in parent_classes):
            raise Exception("Warning: '@parameterized' tests won't work "
                            "inside subclasses of 'TestCase' - use "
                            "'@parameterized.expand' instead")

    def _terrible_magic_get_defining_classes(self):
        """ Returns the set of parent classes of the class currently being defined.
            Will likely only work if called from the ``parameterized`` decorator.
            This function is entirely @brandon_rhodes's fault, as he suggested
            the implementation: http://stackoverflow.com/a/8793684/71522
            """
        stack = inspect.stack()
        if len(stack) <= 4:
            return []
        frame = stack[4]
        code_context = frame[4] and frame[4][0].strip()
        if not (code_context and code_context.startswith("class ")):
            return []
        _, _, parents = code_context.partition("(")
        parents, _, _ = parents.partition(")")
        return eval("[" + parents + "]", frame[0].f_globals, frame[0].f_locals)

    @classmethod
    def input_as_callable(cls, input):
        if callable(input):
            return lambda: cls.check_input_values(input())
        input_values = cls.check_input_values(input)
        return lambda: input_values

    @classmethod
    def check_input_values(cls, input_values):
        if not hasattr(input_values, "__iter__"):
            raise ValueError("expected iterable input; got %r" %(input, ))
        return input_values

    @classmethod
    def expand(cls, input, testcase_func_name=None, testcase_func_doc=None):
        """ A "brute force" method of parameterizing test cases. Creates new
            test cases and injects them into the namespace that the wrapped
            function is being defined in. Useful for parameterizing tests in
            subclasses of 'UnitTest', where Nose test generators don't work.

            >>> @parameterized.expand([("foo", 1, 2)])
            ... def test_add1(name, input, expected):
            ...     actual = add1(input)
            ...     assert_equal(actual, expected)
            ...
            >>> locals()
            ... 'test_add1_foo_0': <function ...> ...
            >>>
            """

        def parameterized_expand_wrapper(f, instance=None):
            stack = inspect.stack()
            frame = stack[1]
            frame_locals = frame[0].f_locals

            base_name = f.__name__
            get_input = cls.input_as_callable(input)
            for num, args in enumerate(get_input()):
                p = param.from_decorator(args)
                if testcase_func_name:
                    # Caller wants to over-ride default test case func/method naming scheme.
                    name = testcase_func_name(f, num, p)
                else:
                    name_suffix = "_%s" %(num, )
                    if len(p.args) > 0 and isinstance(p.args[0], string_types):
                        name_suffix += "_" + cls.to_safe_name(p.args[0])
                    name = base_name + name_suffix

                testcase_func_doc_func = (testcase_func_doc or default_testcase_func_doc)
                doc = testcase_func_doc_func(f, num, p)

                frame_locals[name] = cls.param_as_standalone_func(p, f, name)
                frame_locals[name].__doc__ = doc
            return nottest(f)
        return parameterized_expand_wrapper

    @classmethod
    def param_as_standalone_func(cls, p, func, name):
        @wraps(func)
        def standalone_func(*a):
            return func(*(a + p.args), **p.kwargs)

        standalone_func.__name__ = name
        return standalone_func

    @classmethod
    def to_safe_name(cls, s):
        return str(re.sub("[^a-zA-Z0-9_]+", "_", s))
