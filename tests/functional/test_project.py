"""Contains tests for the project module"""

from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory

from ns_poet import project as mod_ut


def test_project_config():
    """Should load project config"""
    with TemporaryDirectory() as tmpdirname:
        with Path(tmpdirname).joinpath("pyproject.toml").open("w") as f:
            f.write(
                """
[tool.nspoet]
import_map_path = "3rdparty/python/import-map.json"
requirements_path = "3rdparty/python/requirements.txt"
"""
            )

        run(["git", "init"], cwd=tmpdirname)
        config = mod_ut.PoetProject.from_path(Path(tmpdirname))
        assert str(config.import_map_path).endswith("3rdparty/python/import-map.json")
        assert str(config.requirements_path).endswith(
            "3rdparty/python/requirements.txt"
        )
