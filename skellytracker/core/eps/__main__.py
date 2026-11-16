"""`python -m skellytracker.core.eps` runs the CLI `skellytracker-eps`."""

import sys

from skellytracker.core.eps.cli import main

if __name__ == "__main__":
    sys.exit(main())
