"""Contains base BuildTarget class"""
from abc import ABC
from functools import total_ordering
from typing import Any


@total_ordering
class BuildTarget(ABC):
    """Represents a Python build target in Pants.

    This should be used as a mixin to provide common attributes and methods.
    """

    # This string will be used as an identifier for the build target
    key: str = None

    def __str__(self) -> str:
        """String representation"""
        return str(self.key)

    def __eq__(self, other: Any) -> bool:
        """Equality check"""
        if hasattr(other, "key"):
            return str(self.key) == str(other.key)
        else:
            return False

    def __hash__(self) -> int:
        """Object hash"""
        return hash((str(self.key),))

    def __repr__(self) -> str:
        """Object representation for debugging"""
        return str(self.key)

    def __lt__(self, other: Any) -> bool:
        """Less than comparator"""
        if hasattr(other, "key"):
            return str(self.key) < str(other.key)
        else:
            return False

    @property
    def dependency_target(self) -> str:
        """Returns the representation of this target in another target's dependencies"""
        return str(self.key)
