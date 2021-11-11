"""Contains PoetPackage class"""

from pathlib import Path
from typing import Any, Dict, MutableMapping, Optional

import toml


class PoetPackage:
    """Class that represents a package managed by ns-poet

    This object manages a Python package's pyproject.toml (i.e. manifest) file.

    The schema for the configuration file in the git project root is::

        [tool.nspoet]
        generate_package_manifest = true

    """

    def __init__(self, package_path: Path) -> None:
        """Initializer

        Args:
            package_path: Path to the package

        """
        self.package_path = package_path
        self.config_file_path = package_path.joinpath("pyproject.toml")
        self._config: Optional[MutableMapping[str, Any]] = None

    @classmethod
    def from_path(cls, package_path: Path) -> "PoetPackage":
        """Create a package object and load configuration from a given package path

        Args:
            package_path: Path to the package

        Returns:
            new PoetPackage instance

        """
        p = cls(package_path)
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

    def save_config(self) -> None:
        """Save the configuration object to disk"""
        if self.generate_package_manifest:
            with self.config_file_path.open("w") as f:
                toml.dump(  # type: ignore
                    self._config,
                    f,
                    encoder=toml.encoder.TomlPreserveInlineDictEncoder(),  # type: ignore
                )

    def to_string(self) -> str:
        """Dump the configuration to a TOML string"""
        return toml.dumps(  # type: ignore
            self._config, encoder=toml.encoder.TomlPreserveInlineDictEncoder()  # type: ignore
        )

    @property
    def package_config(self) -> Dict[str, Any]:
        """Return the nspoet configuration subsection within the manifest"""
        return self._config.get("tool", {}).get("nspoet", {})

    @property
    def generate_package_manifest(self) -> bool:
        """Flag denoting whether to generate a package manifest file"""
        return self.package_config.get("generate_package_manifest", True)

    def update(
        self, name: str, dependencies: Dict[str, str], dev_dependencies: Dict[str, str]
    ) -> None:
        """Update the package configuration in place

        Args:
            name: package name
            dependencies: map of dependency name to version specifier
            dev_dependencies: map of development dependency name to version specifier

        """
        self._config.setdefault("tool", {})
        self._config["tool"].setdefault("poetry", {})
        self._config["tool"]["poetry"]["name"] = name
        self._config["tool"]["poetry"]["version"] = "1.0.0"
        self._config["tool"]["poetry"]["description"] = ""
        self._config["tool"]["poetry"]["authors"] = []
        self._config["tool"]["poetry"]["license"] = "Proprietary"
        self._config["tool"]["poetry"]["dependencies"] = dependencies
        self._config["tool"]["poetry"]["dev-dependencies"] = dev_dependencies
        self._config["build-system"] = {
            "requires": ["poetry-core>=1.0.0"],
            "build-backend": "poetry.core.masonry.api",
        }
