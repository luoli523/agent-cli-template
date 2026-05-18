"""Allow ``python -m mycli`` invocation in addition to the ``mycli`` script."""

import sys

from mycli.cli import main

if __name__ == "__main__":
    sys.exit(main())
