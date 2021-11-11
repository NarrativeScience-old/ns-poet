"""Contains a configuration parser and project config singleton"""
import json
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, MutableMapping, Optional, Union

import pkg_resources
from pkg_resources import Requirement
import toml

from .util import get_git_top_level_path


class PoetProject:
    """Project object

    This object parses project configuration and manages the import map associated with
    the project's requirements.txt file.

    The schema for the configuration file in the git project root is::

        [tool.nspoet]
        ignore_dirs = []
        ignore_targets = []
        import_map_path = "3rdparty/python/import-map.json"
        requirements_path = "3rdparty/python/requirements.txt"
        top_dirs = ["."]
        default_python_version = "^3.6.5"

    """

    def __init__(self, project_path: Union[str, Path]) -> None:
        """Initializer

        Args:
            project_path: Path to the project

        """
        self.project_path = Path(project_path)
        self.config_file_path = self.project_path.joinpath("pyproject.toml")
        self._config: Optional[MutableMapping[str, Any]] = None
        self._requirements: Optional[Dict[str, Requirement]] = None
        self._import_map: Optional[Dict[str, str]] = None

    @classmethod
    def from_path(cls, project_path: Path) -> "PoetProject":
        """Create a project object and load configuration from a given project path

        Args:
            project_path: path to the project (git repo root)

        Returns:
            new PoetProject instance

        """
        p = cls(project_path)
        p.load_config()
        return p

    def load_config(self) -> MutableMapping[str, Any]:
        """Load configuration from disk

        Returns:
            configuration dict

        """
        if self.config_file_path.is_file():
            with self.config_file_path.open() as f:
                self._config = toml.load(f)
        else:
            self._config = {}

        return self._config

    @property
    def project_config(self) -> Dict[str, Any]:
        """Return the nspoet configuration subsection within the manifest"""
        return self._config.get("tool", {}).get("nspoet", {})

    @property
    def ignore_dirs(self) -> FrozenSet[str]:
        """Never look for or process files in this set of directories"""
        return frozenset(self.project_config.get("ignore_dirs", []))

    @property
    def ignore_targets(self) -> FrozenSet[str]:
        """Set of target package names to ignore when collecting build targets"""
        return frozenset(self.project_config.get("ignore_targets", []))

    @property
    def import_map_path(self) -> Path:
        """Path to the location of the import-map.json file within the project root

        This file contains a map from the import name found in *.py to the library's
        project name (i.e. requirements.txt name).

        """
        return self.project_path.joinpath(
            self.project_config.get(
                "import_map_path",
                "import-map.json",
            )
        )

    @property
    def requirements_path(self) -> Path:
        """Path to the requirements.txt within the project root"""
        return self.project_path.joinpath(
            self.project_config.get(
                "requirements_path",
                "requirements.txt",
            )
        )

    @property
    def top_dirs(self) -> List[str]:
        """Top-level directories to search for Python packages"""
        return self.project_config.get("top_dirs", ["."])

    @property
    def default_python_version(self) -> str:
        """Default python version to set in package manifests"""
        return self.project_config.get("default_python_version", "^3.6.5")

    def load_requirements(self) -> Dict[str, Requirement]:
        """Load requirement specifiers from disk

        Returns:
            map of requirement name/project name to requirement object

        """
        if not self._requirements:
            self._requirements = {}
            with self.requirements_path.open() as f:
                for r in pkg_resources.parse_requirements(f.read()):
                    self._requirements[r.unsafe_name] = r
                    self._requirements[r.project_name] = r

        return self._requirements

    def get_requirement(self, name: str) -> Requirement:
        """Get a requirement by name"""
        return self._requirements[name]

    def load_import_map(self) -> Dict[str, str]:
        """Load import map from disk

        Returns:
            map of import name to project name or empty dict if no file found

        """
        try:
            with self.import_map_path.open() as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def get_import_map(self) -> Dict[str, str]:
        """Get the import map or load it if not already cached

        Returns:
            map of import name to project name

        """
        if not self._import_map:
            self._import_map = self.load_import_map()

        return self._import_map

    def update_import_map(self, import_map: Dict[str, str]) -> None:
        """Update import map file on disk

        Args:
            import_map: map of import name to project name

        """
        with self.import_map_path.open("w") as f:
            json.dump(import_map, f, sort_keys=True, indent=2)
            f.write("\n")


# Create a singleton for the project configuration
PROJECT_CONFIG = PoetProject.from_path(get_git_top_level_path())
