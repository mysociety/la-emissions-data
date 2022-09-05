import rich_click as click
from .convert_emissions import convert_emissions
from .compare_emissions import generate_comparisons

def build_data():
    convert_emissions()
    generate_comparisons()

@click.group()
def cli():
    pass


def main():
    cli()


@cli.command()
def build():
    build_data()

if __name__ == "__main__":
    main()
