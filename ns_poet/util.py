"""Utility functions"""

import ast
from pathlib import Path
import subprocess
from typing import Set


class ModuleImportVisitor(ast.NodeVisitor):
    """AST visitor for collecting imports from a module"""

    def __init__(self) -> None:
        self.imports = set()

    def visit_ImportFrom(self, node) -> None:
        """Collect an import when specified as `from foo import bar`"""
        if node.module is not None:
            self.imports.add(node.module.split(".")[0])

    def visit_Import(self, node) -> None:
        """Collect an import when specified as `import foo`"""
        self.imports.add(node.names[0].name.split(".")[0])


def gather_dependencies_from_module(path: str) -> Set[str]:
    """Gather a set of other build targets from a single Python module

    Args:
        path: Python module path

    Returns:
        set of package names that were imported in the module

    """
    with open(path) as f:
        contents = f.read()
    tree = ast.parse(contents)
    visitor = ModuleImportVisitor()
    visitor.visit(tree)
    return visitor.imports


def get_git_top_level_path() -> Path:
    """Get the path of the git repository where this CLI is running"""
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], check=True, stdout=subprocess.PIPE
    )
    output = proc.stdout.decode("utf-8").strip()
    return Path(output)


def write_package_config_file(config_file_path: Path, contents: str) -> None:
    with config_file_path.open("w") as f:
        f.write(contents + "\n")
