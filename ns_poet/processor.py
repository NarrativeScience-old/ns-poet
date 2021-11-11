"""Contains package processor class"""
import logging
from multiprocessing import Pool
import os
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple

import networkx as nx

from .exceptions import (
    CircularImportsFound,
    DuplicateTarget,
    MultipleSourcePackagesFound,
)
from .package_targets import PythonPackage
from .project import PROJECT_CONFIG
from .util import gather_dependencies_from_module, write_package_config_file

logger = logging.getLogger(__name__)

# Number of workers to use for various multiprocessing pools
PROCESSES = max(1, os.cpu_count() - 1)


class PackageProcessor:
    """Class with methods for processing internal Python packages in order to:

    * Check for circular imports
    * Generate Pants BUILD files
    * Determine package dependencies
    """

    def __init__(self) -> None:
        """Initializer"""
        # Map of target key to instance of a Python package build target
        self._targets: Dict[str, PythonPackage] = {}
        # Graph of targets
        self._target_graph: nx.DiGraph = None

    def get_target(self, target_key: str) -> PythonPackage:
        """Get a registered target by key

        Args:
            target_key: Key under which the target was registered

        Returns:
            target/package object

        """
        return self._targets[target_key]

    def register_packages(self) -> None:
        """Register targets and their dependencies.

        This should be called before performing an action with the packages.
        """
        self._register_task_targets_code()
        # self._register_task_targets_py2sfn_projects()
        # self._register_task_targets_tests()
        # self._register_extra_targets()
        self._gather_dependencies()
        self._build_target_graph()

    def _gather_dependencies(self) -> None:
        """Gather dependencies for each target"""
        logger.info("Gathering dependencies")

        # Collect a list of (build target, Python module) pairs from *all* the targets
        target_paths: List[Tuple[PythonPackage, str]] = []
        for target in self._targets.values():
            target_paths.extend(target.find_target_paths())

        # Create a pool of workers that will parse imports from each Python module
        # path.
        paths = [path for _, path in target_paths]
        with Pool(processes=PROCESSES) as pool:
            # Return a list of sets containing imported package names
            imported_package_names_per_path = pool.map(
                gather_dependencies_from_module, paths
            )

        # For each target path / package name pair, process and add the dependency to
        # the target's set of dependencies.
        for (target, _), (path, package_names) in zip(
            target_paths, imported_package_names_per_path
        ):
            for package_name in package_names:
                target.add_dependency(self._targets, path, package_name)

        # Allow each target to set extra dependencies based on their own custom logic.
        # For most targets this will be a no-op.
        for target in self._targets.values():
            target.set_extra_dependencies(self._targets)

    def generate_package_manifests(self, target_pattern: Optional[str] = None) -> None:
        """Generate package manifest files.

        You must have already called :py:meth:`.register_packages`.

        Args:
            target_pattern: If provided, pyproject.toml files are only generated for
                targets with keys matching the pattern

        """
        logger.info("Generating package manifest files")
        targets_to_save = []
        for key, target in self._targets.items():
            if not target_pattern or re.search(target_pattern, key):
                target.generate_package_manifest()
                targets_to_save.append(
                    (target.config.config_file_path, target.config.to_string())
                )

        # Create a pool of workers that will render, format, and write each manifest
        # file to disk.
        with Pool(processes=PROCESSES) as pool:
            pool.starmap(write_package_config_file, targets_to_save)

    def generate_package_manifest(self, package_path: Path) -> None:
        """Generate package manifest file for a single target.

        You must have already called :py:meth:`.register_packages`.

        Args:
            package_path: path to a Python package

        """
        p = PythonPackage(package_path)
        target = self._targets[p.package_name]
        target.generate_package_manifest()
        target.config.save_config()

    def _register_task_targets_code(self) -> None:
        """Register task targets for code packages

        This iterates through various directories looking for a setup.py file. If it
        finds one, it means we've found a Python package and can register a build
        target.
        """
        logger.info("Registering code targets")

        setup_py_paths: List[Tuple[str, Path]] = []
        for top_dir_name in PROJECT_CONFIG.top_dirs:
            top_dir = PROJECT_CONFIG.project_path.joinpath(top_dir_name)
            logger.debug(f"Walking {top_dir}")
            for dirpath, dirnames, filenames in os.walk(top_dir):
                if os.path.basename(dirpath) in PROJECT_CONFIG.ignore_dirs:
                    # Empty the list of directories so os.walk does not recur
                    dirnames.clear()
                else:
                    for filename in filenames:
                        if filename == "setup.py":
                            setup_py_paths.append(
                                (top_dir_name, Path(dirpath).joinpath(filename))
                            )

        for top_dir_name, setup_py_path in setup_py_paths:
            logger.debug(f"Registering {setup_py_path}")

            src_dir = setup_py_path.parent.joinpath("src")
            if not src_dir.is_dir():
                continue
            src_entries = [
                src_entry
                for src_entry in os.scandir(src_dir)
                if (
                    src_entry.is_dir()
                    and "egg-info" not in src_entry.path
                    and "pycache" not in src_entry.path
                )
            ]
            if len(src_entries) == 0:
                logger.debug(f"No entries found in {src_dir}")
                continue
            elif len(src_entries) > 1:
                raise MultipleSourcePackagesFound(
                    f"More than one package found in {src_dir}:"
                    f" {src_entries}. This could be caused by old git"
                    " state. Either manually clean up the packages or"
                    " run `git clean -fxd` if you are OK with a"
                    " completely clean slate."
                )

            src_entry = src_entries[0]
            package_name = os.path.basename(src_entry.path)
            target = PythonPackage(setup_py_path.parent)
            if target.key in PROJECT_CONFIG.ignore_targets:
                logger.debug(f"Ignoring {target}")
            elif package_name in self._targets:
                raise DuplicateTarget(
                    f"Duplicate target found for {package_name}. Check the"
                    " git repository for old folders that have the same"
                    " name."
                )
            else:
                self._targets[package_name] = target
                logger.debug(f"Registered target {target}")

    def _build_target_graph(self) -> None:
        """Build a graph of package targets.

        This is used to check for cycles and compute dependencies.
        """
        G = nx.DiGraph()
        for target in self._targets.values():
            G.add_node(target)
            for dependency in target.dependencies:
                G.add_edge(target, dependency)
        self._target_graph = G

    def ensure_no_circular_imports(self) -> None:
        """Ensure there are no circular imports in any of the processed packages

        You must have already called :py:meth:`.register_packages`.

        Raises:
            :py:exec:`.CircularImportsFound` if any circular imports were found

        """
        logger.info("Ensuring no circular imports")
        cycles = list(nx.simple_cycles(self._target_graph))
        if len(cycles) > 0:
            raise CircularImportsFound(cycles)
