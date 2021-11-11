"""Contains PoetPackage class"""

from pathlib import Path
from typing import Any, Dict, Optional

import toml

from ns_poet.project import PROJECT_CONFIG


class PoetPackage:
    """Class that represents a package managed by ns-poet"""

    def __init__(self, package_path: Path) -> None:
        """Initializer

        Args:
            package_path: Path to the package

        """
        self.package_path = package_path
        self.config_file_path = package_path.joinpath("pyproject.toml")
        self._config: Optional[Dict[str, Any]] = None

    @classmethod
    def from_path(cls, package_path: Path) -> "PoetPackage":
        p = cls(package_path)
        p.load_config()
        return p

    def load_config(self) -> Dict[str, Any]:
        if self.config_file_path.is_file():
            with self.config_file_path.open() as f:
                self._config = toml.load(f)
        else:
            self._config = {}

        return self._config

    def save_config(self) -> None:
        if self.generate_package_manifest:
            with self.config_file_path.open("w") as f:
                toml.dump(self._config, f)

    def to_string(self) -> str:
        return toml.dumps(self._config)

    @property
    def package_config(self) -> Dict[str, Any]:
        return self._config.get("tool", {}).get("nspoet", {})

    @property
    def generate_package_manifest(self) -> bool:
        """Flag denoting whether to generate a package manifest file"""
        return self.package_config.get("generate_package_manifest", True)

    def update(
        self, name, dependencies: Dict[str, str], dev_dependencies: Dict[str, str]
    ) -> None:
        self._config.setdefault("tool", {})
        self._config["tool"].setdefault("poetry", {})
        self._config["tool"]["poetry"]["name"] = name
        self._config["tool"]["poetry"]["version"] = "1.0.0"
        self._config["tool"]["poetry"]["description"] = ""
        self._config["tool"]["poetry"]["authors"] = []
        self._config["tool"]["poetry"]["license"] = "Proprietary"

        self._config["tool"]["poetry"]["dependencies"] = dependencies
        self._config["tool"]["poetry"]["dependencies"][
            "python"
        ] = PROJECT_CONFIG.default_python_version

        self._config["tool"]["poetry"].setdefault("dev-dependencies", {})

        self._config["build-system"] = {
            "requires": ["poetry-core>=1.0.0"],
            "build-backend": "poetry.core.masonry.api",
        }
        print(self._config)
