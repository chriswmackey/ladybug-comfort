"""ladybug-comfort commands."""

try:
    import click
except ImportError:
    raise ImportError(
        'click module is not installed. Try `pip install ladybug-comfort[cli]` command.'
    )

import logging

from ladybug_comfort.cli.energyplus import energyplus


@click.group()
@click.version_option()
def main():
    pass


_logger = logging.getLogger(__name__)


@main.command('viz')
def viz():
    """Check if ladybug is flying!"""
    click.echo('viiiiiiiiiiiiizzzzzzzzz!')


main.add_command(energyplus)


if __name__ == "__main__":
    main()
