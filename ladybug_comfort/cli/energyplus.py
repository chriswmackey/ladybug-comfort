"""Parse energyplus thermal results and run them through comfort models."""

try:
    import click
except ImportError:
    raise ImportError(
        'click is not installed. Try `pip install . [cli]` command.'
    )

import sys
import os
import logging
import json

_logger = logging.getLogger(__name__)


@click.group(help='Commands for running energyplus results through comfort models.')
def energyplus():
    pass

