import sys
from distutils.core import setup

if __name__ == "__main__":
    if "sdist" not in sys.argv[1:]:
        raise ValueError("Please use the 'parameterized' (note the second 'e' in 'parameterized') pypi package instead of 'nose-parametrized'")
    setup(
        name="nose-parametrized",
        version="0.1",
        description="Please use the 'parameterized' package (note the second 'e' in 'parameterized')",
    )
