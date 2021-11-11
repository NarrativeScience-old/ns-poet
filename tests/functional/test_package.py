"""Contains tests for the package module"""

from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory

from ns_poet import package as mod_ut


def test_package_config():
    """Should load package config"""
    with TemporaryDirectory() as tmpdirname:
        with Path(tmpdirname).joinpath("pyproject.toml").open("w") as f:
            f.write(
                """
[tool.nspoet]
generate_package_manifest = false
"""
            )

        run(["git", "init"], cwd=tmpdirname)
        config = mod_ut.PoetPackage.from_path(Path(tmpdirname))
        assert not config.generate_package_manifest
