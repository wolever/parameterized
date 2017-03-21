from .parameterized import parameterized, param

import os
import warnings
if not os.environ.get("NOSE_PARAMETERIZED_NO_WARN"):
    warnings.warn(
        "The 'nose-parameterized' package has been renamed 'parameterized'. "
        "For the two step migration instructions, see: "
        "https://github.com/wolever/parameterized#migrating-from-nose-parameterized-to-parameterized "
        "(set NOSE_PARAMETERIZED_NO_WARN=1 to suppress this warning)"
    )
