import sys
from distutils.core import setup

if __name__ == "__main__":
    if "sdist" not in sys.argv[1:]:
        raise ValueError("please use the 'nose-parameterized' pypi package instead of 'nose-parametrized'")
    setup(
        name="nose-parametrized",
        version="0.0",
        description="please use 'nose-parameterized' for installation",
    )
