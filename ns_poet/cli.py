"""Contains the CLI"""

import logging
from pathlib import Path
from typing import Optional

import click

from ns_poet.processor import PackageProcessor
from ns_poet.project import PROJECT_CONFIG
from ns_poet.requirements import update_import_map

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def cli() -> None:
    """Autogenerate Poetry package manifests in a monorepo"""
    pass


@cli.group(name="import-map")
def import_map() -> None:
    """Commands for managing imports"""
    pass


@import_map.command()
def update() -> None:
    """Update an import map from requirements.txt"""
    update_import_map()


@cli.group()
def package() -> None:
    """Commands for managing packages"""
    pass


@package.command()
@click.option(
    "-p",
    "--package-path",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, path_type=Path),
    help="Generate a package manifest for a single package path",
)
def generate(package_path: Optional[Path]) -> None:
    """Generate Poetry package manifests"""
    PROJECT_CONFIG.load_requirements()
    processor = PackageProcessor()
    processor.register_packages()
    processor.ensure_no_circular_imports()
    if package_path:
        processor.generate_package_manifest(package_path)
    else:
        processor.generate_package_manifests()
