"""Static examples checked by mypy; not collected by test runners."""
from typing import Any, Callable
from unittest import TestCase
from parameterized import param, parameterized, parameterized_class

def mark(function: Callable[..., Any]) -> Callable[..., Any]:
    return function

class Example(TestCase):
    @parameterized.expand([param("one", expected=3)], decorators=[mark])
    def test_value(self, value: str, expected: int) -> None:
        self.assertEqual(len(value), expected)

@parameterized([1, 2])
def test_generator(value: int) -> None:
    assert value > 0

@parameterized_class([{"value": 42}])
class ClassExample(TestCase):
    value: int
    def test_value(self) -> None:
        self.assertEqual(self.value, 42)
