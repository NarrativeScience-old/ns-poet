"""Contains base PythonPackage class"""
import logging
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple, Union

from toml.decoder import InlineTableDict

from ns_poet.package import PoetPackage
from ns_poet.project import PROJECT_CONFIG
from .base import BuildTarget
from .requirement import PythonRequirement

logger = logging.getLogger(__name__)


class DynamicInlineTableDict(dict, InlineTableDict):
    """Subclass for inline tables in TOML"""


class PythonPackage(BuildTarget):
    """Represents a Python package (e.g. lib or test) build target in Pants"""

    def __init__(
        self,
        package_path: Union[str, Path],
    ) -> None:
        """Initializer

        Args:
            package_path: Path to the package directory, e.g. lib/python_core

        """
        self.package_path = Path(package_path)

        # This string will be used as an identifier for the build target
        self.key = str(package_path)

        # Set of dependencies to be gathered later
        self.dependencies: Set[BuildTarget] = set()
        self.dev_dependencies: Set[BuildTarget] = set()

        # Load the package config
        self.config = PoetPackage.from_path(self.package_path)

    @property
    def package_name(self) -> str:
        """Python package name

        Raises:
            :py:exc:`ValueError`: if no package name could be parsed from the directory
                structure

        Returns:
            package name string

        """
        for p in self.package_path.joinpath("src").iterdir():
            if p.is_dir() and not p.name.endswith(".egg-info"):
                return p.name

        raise ValueError("Could not determine package_name")

    def find_target_paths(self) -> List[Tuple["PythonPackage", str]]:
        """Find a list of target paths for parsing dependencies

        This default implementation collects all the .py files. Subclasses may override
        this method to collect different file types.

        Returns:
            list of tuples with items:
            * the current target (to indicate the owner)
            * the path to the file that will be parsed

        """
        target_paths = []
        for dirpath, dirnames, filenames in os.walk(self.package_path):
            if os.path.basename(dirpath) in PROJECT_CONFIG.ignore_dirs:
                # Empty the list of directories so os.walk does not recur
                dirnames.clear()
            else:
                for filename in filenames:
                    if filename.endswith(".py"):
                        target_paths.append((self, os.path.join(dirpath, filename)))

        return target_paths

    def add_dependency(
        self, targets: Dict[str, "PythonPackage"], module_path: str, package_name: str
    ) -> None:
        """Add a new dependency to the set

        A child class may choose to implement ``set_dependencies`` and skip this method.

        Args:
            targets: map of package name to instance of BuildTarget
            module_path: path of the module that was parsed for imports
            package_name: dependency package name, as parsed from an import statement

        """
        logger.debug(f"Processing {module_path}:{package_name}")
        if package_name in targets and package_name != self.package_name:
            if "tests" in Path(module_path).parts:
                self.dev_dependencies.add(targets[package_name])
                logger.debug(
                    f"Added dev dependency for existing target: {targets[package_name]}"
                )
            else:
                self.dependencies.add(targets[package_name])
                logger.debug(
                    f"Added dependency for existing target: {targets[package_name]}"
                )
            return

        import_map = PROJECT_CONFIG.get_import_map()
        if package_name in import_map:
            if "tests" in Path(module_path).parts:
                self.dev_dependencies.add(PythonRequirement(import_map[package_name]))
                logger.debug(
                    f"Added third-party dev dependency: {import_map[package_name]}"
                )
            else:
                self.dependencies.add(PythonRequirement(import_map[package_name]))
                logger.debug(
                    f"Added third-party dependency: {import_map[package_name]}"
                )

    def set_extra_dependencies(self, targets: Dict[str, "PythonPackage"]) -> None:
        """Set extra dependencies on the target

        This method allows targets to add dependencies based on their own custom logic.
        By default this is a no-op.

        A standard thing to do would be to call
        ``self.add_dependency(targets, package_name)`` one or more times.

        Args:
            targets: map of package name to instance of BuildTarget

        """
        pass

    def convert_dependencies(self, dependencies: Set[BuildTarget]) -> Dict[str, str]:
        """Convert dependencies into a map suitable for dumping to TOML format

        Args:
            dependencies: set of dependencies

        Raises:
            :py:exc:`NotImplementedError`: if dependency is not a requirement or Python
                package

        Returns:
            map of project name to version specifier

        """
        converted = {}
        for dependency in dependencies:
            if isinstance(dependency, PythonRequirement):
                requirement = PROJECT_CONFIG.get_requirement(dependency.key)
                version = str(requirement.specifier)  # type: ignore
                converted[requirement.unsafe_name] = version if version else "*"
            elif isinstance(dependency, PythonPackage):
                converted[dependency.package_name] = DynamicInlineTableDict(
                    path=os.path.relpath(dependency.package_path, self.package_path),
                    develop=True,
                )  # type: ignore
            else:
                raise NotImplementedError(dependency)

        # Sort by key
        converted = {
            k: v for k, v in sorted(converted.items(), key=lambda item: item[0].lower())
        }

        return converted

    def generate_package_manifest(self) -> None:
        """Generate a Poetry package manifest for the build target"""
        dependencies = {"python": PROJECT_CONFIG.default_python_version}
        dependencies.update(self.convert_dependencies(self.dependencies))
        dev_dependencies = self.convert_dependencies(
            self.dev_dependencies - self.dependencies
        )
        self.config.update(self.package_name, dependencies, dev_dependencies)
