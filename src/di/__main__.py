"""Allow ``python -m di`` invocation in addition to the ``di`` script."""

import sys

from di.cli import main

if __name__ == "__main__":
    sys.exit(main())
