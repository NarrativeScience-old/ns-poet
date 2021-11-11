"""Contains tests for the processor module"""

from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
from unittest.mock import patch

from ns_poet import processor as mod_ut


@patch("ns_poet.project.get_git_top_level_path")
def test_register_packages__empty(mock_get_git_top_level_path):
    """Should register no packages"""
    with TemporaryDirectory() as tmpdirname:
        mock_get_git_top_level_path.return_value = tmpdirname
        with Path(tmpdirname).joinpath("pyproject.toml").open("w") as f:
            f.write(
                """
[tool.nspoet]
import_map_path = "3rdparty/python/import-map.json"
requirements_path = "3rdparty/python/requirements.txt"
"""
            )

        run(["git", "init"], cwd=tmpdirname)
        processor = mod_ut.PackageProcessor()
        processor.register_packages()
        assert processor._targets == {}
