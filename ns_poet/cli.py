"""Contains the CLI"""

import logging
from pathlib import Path
import subprocess
from typing import Optional

import click

from ns_poet.processor import PackageProcessor
from ns_poet.project import PROJECT_CONFIG
from ns_poet.requirements import update_import_map

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
def cli() -> None:
    """Manage Poetry packages in a monorepo"""
    pass


@cli.group(name="import-map")
def import_map() -> None:
    """Commands for managing the import map"""
    pass


@import_map.command()
def update() -> None:
    """Update the import map from requirements.txt"""
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


@package.command()
@click.option(
    "-p",
    "--package-path",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, path_type=Path),
    help="Install a single package at the given path",
)
def install(package_path: Optional[Path]) -> None:
    """Install Poetry packages"""
    if package_path:
        click.secho(f"Installing {package_path}...", fg="white", bold=True)
        subprocess.run(["poetry", "install"], cwd=str(package_path), check=True)
        click.secho(f"Installed {package_path}", fg="green", bold=True)
    else:
        for top_dir in PROJECT_CONFIG.top_dirs:
            for path in PROJECT_CONFIG.project_path.joinpath(top_dir).glob(
                "**/pyproject.toml"
            ):
                if any(
                    ignore_dir in str(path) for ignore_dir in PROJECT_CONFIG.ignore_dirs
                ):
                    click.secho(f"Ignoring {path.parent}...", fg="white")
                    continue

                click.secho(f"Installing {path.parent}...", fg="white", bold=True)
                subprocess.run(["poetry", "install"], cwd=str(path.parent), check=True)
                click.secho(f"Installed {path.parent}", fg="green", bold=True)
