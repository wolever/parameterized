import re
import new
import inspect
import logging
import logging.handlers
from functools import wraps

from nose.tools import nottest
from unittest import TestCase


def _terrible_magic_get_defining_classes():
    """ Returns the set of parent classes of the class currently being defined.
        Will likely only work if called from the ``parameterized`` decorator.
        This function is entirely @brandon_rhodes's fault, as he suggested
        the implementation: http://stackoverflow.com/a/8793684/71522
        """
    stack = inspect.stack()
    if len(stack) <= 4:
        return []
    frame = stack[3]
    code_context = frame[4][0].strip()
    if not code_context.startswith("class "):
        return []
    _, parents = code_context.split("(", 1)
    parents, _ = parents.rsplit(")", 1)
    return eval("[" + parents + "]", frame[0].f_globals, frame[0].f_locals)

def parameterized(input):
    """ Parameterize a test case:
        >>> add1_tests = [(1, 2), (2, 3)]
        >>> class TestFoo(object):
        ...     @parameterized(add1_tests)
        ...     def test_add1(self, input, expected):
        ...         assert_equal(add1(input), expected)
        >>> @parameterized(add1_tests)
        ... def test_add1(input, expected):
        ...     assert_equal(add1(input), expected)
        >>>
        """

    if not hasattr(input, "__iter__"):
        raise ValueError("expected iterable input; got %r" %(input, ))

    def parameterized_helper(f):
        attached_instance_method = [False]

        parent_classes = _terrible_magic_get_defining_classes()
        if any(issubclass(cls, TestCase) for cls in parent_classes):
            raise Exception("Warning: '@parameterized' tests won't work "
                            "inside subclasses of 'TestCase' - use "
                            "'@parameterized.expand' instead")

        @wraps(f)
        def parameterized_helper_method(self=None):
            if self is not None and not attached_instance_method[0]:
                # confusingly, we need to create a named instance method and
                # attach that to the class...
                cls = self.__class__
                im_f = new.instancemethod(f, None, cls)
                setattr(cls, f.__name__, im_f)
                attached_instance_method[0] = True
            for args in input:
                if isinstance(args, basestring):
                    args = [args]
                # ... then pull that named instance method off, turning it into
                # a bound method ...
                if self is not None:
                    args = [getattr(self, f.__name__)] + list(args)
                else:
                    args = [f] + list(args)
                # ... then yield that as a tuple. If those steps aren't
                # followed precicely, Nose gets upset and doesn't run the test
                # or doesn't run setup methods.
                yield tuple(args)

        f.__name__ = "_helper_for_%s" %(f.__name__, )
        parameterized_helper_method.parameterized_input = input
        parameterized_helper_method.parameterized_func = f
        return parameterized_helper_method

    return parameterized_helper

def to_safe_name(s):
    return re.sub("[^a-zA-Z0-9_]", "", s)

def parameterized_expand_helper(func_name, func, args):
    def parameterized_expand_helper_helper(self=()):
        if self != ():
            self = (self, )
        return func(*(self + args))
    parameterized_expand_helper_helper.__name__ = func_name
    return parameterized_expand_helper_helper

def parameterized_expand(input):
    """ A "brute force" method of parameterizing test cases. Creates new test
        cases and injects them into the namespace that the wrapped function
        is being defined in. Useful for parameterizing tests in subclasses
        of 'UnitTest', where Nose test generators don't work.

        >>> @parameterized.expand([("foo", 1, 2)])
        ... def test_add1(name, input, expected):
        ...     actual = add1(input)
        ...     assert_equal(actual, expected)
        ...
        >>> locals()
        ... 'test_add1_foo_0': <function ...> ...
        >>>
        """

    def parameterized_expand_wrapper(f):
        stack = inspect.stack()
        frame = stack[1]
        frame_locals = frame[0].f_locals

        base_name = f.__name__
        for num, args in enumerate(input):
            name_suffix = "_%s" %(num, )
            if len(args) > 0 and isinstance(args[0], basestring):
                name_suffix += "_" + to_safe_name(args[0])
            name = base_name + name_suffix
            new_func = parameterized_expand_helper(name, f, args)
            frame_locals[name] = new_func
        return nottest(f)
    return parameterized_expand_wrapper

parameterized.expand = parameterized_expand

def assert_contains(haystack, needle):
    if needle not in haystack:
        raise AssertionError("%r not in %r" %(needle, haystack))

def assert_not_contains(haystack, needle):
    if needle in haystack:
        raise AssertionError("%r in %r" %(needle, haystack))

def imported_from_test():
    """ Returns true if it looks like this module is being imported by unittest
        or nose. """
    import re
    import inspect
    nose_re = re.compile(r"\bnose\b")
    unittest_re = re.compile(r"\bunittest2?\b")
    for frame in inspect.stack():
        file = frame[1]
        if nose_re.search(file) or unittest_re.search(file):
            return True
    return False

def assert_raises(func, exc_type, str_contains=None, repr_contains=None):
    try:
        func()
    except exc_type as e:
        if str_contains is not None and str_contains not in str(e):
            raise AssertionError("%s raised, but %r does not contain %r"
                                 %(exc_type, str(e), str_contains))
        if repr_contains is not None and repr_contains not in repr(e):
            raise AssertionError("%s raised, but %r does not contain %r"
                                 %(exc_type, repr(e), repr_contains))
        return e
    else:
        raise AssertionError("%s not raised" %(exc_type, ))


log_handler = None
def setup_logging():
    """ Configures a log handler which will capure log messages during a test.
        The ``logged_messages`` and ``assert_no_errors_logged`` functions can be
        used to make assertions about these logged messages.

        For example::

            from ensi_common.testing import (
                setup_logging, teardown_logging, assert_no_errors_logged,
                assert_logged,
            )

            class TestWidget(object):
                def setup(self):
                    setup_logging()

                def teardown(self):
                    assert_no_errors_logged()
                    teardown_logging()

                def test_that_will_fail(self):
                    log.warning("this warning message will trigger a failure")

                def test_that_will_pass(self):
                    log.info("but info messages are ok")
                    assert_logged("info messages are ok")
        """
                    
    global log_handler
    if log_handler is not None:
        logging.getLogger().removeHandler(log_handler)
    log_handler = logging.handlers.BufferingHandler(1000)
    formatter = logging.Formatter("%(name)s: %(levelname)s: %(message)s")
    log_handler.setFormatter(formatter)
    logging.getLogger().addHandler(log_handler)

def teardown_logging():
    global log_handler
    if log_handler is not None:
        logging.getLogger().removeHandler(log_handler)
        log_handler = None

def logged_messages():
    assert log_handler, "setup_logging not called"
    return [ (log_handler.format(record), record) for record in log_handler.buffer ]

def assert_no_errors_logged():
    for _, record in logged_messages():
        if record.levelno >= logging.WARNING:
            # Assume that the nose log capture plugin is being used, so it will
            # show the exception.
            raise AssertionError("an unexpected error was logged")

def assert_logged(expected_msg_contents):
    for msg, _ in logged_messages():
        if expected_msg_contents in msg:
            return
    raise AssertionError("no logged message contains %r"
                         %(expected_msg_contents, ))
