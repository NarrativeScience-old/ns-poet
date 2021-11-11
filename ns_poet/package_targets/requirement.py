"""Contains PythonRequirement class"""
from .base import BuildTarget


class PythonRequirement(BuildTarget):
    """Represents a Python requirement build target"""

    def __init__(self, package_name: str) -> None:
        self.package_name = package_name
        self.key = f"{self.package_name}"
