import rich_click as click
from .convert_emissions import convert_emissions


@click.group()
def cli():
    pass


def main():
    cli()


@cli.command()
def build():
    convert_emissions()


if __name__ == "__main__":
    main()
