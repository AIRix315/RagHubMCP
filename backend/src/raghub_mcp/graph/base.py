"""Base classes and types for code graph analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeType(str, Enum):
    """Types of nodes in code graph."""

    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    IMPORT = "import"


class EdgeType(str, Enum):
    """Types of edges in code graph."""

    IMPORTS = "imports"
    CALLS = "calls"
    DEFINES = "defines"
    INHERITS = "inherits"
    REFERENCES = "references"


@dataclass
class GraphNode:
    """Represents a node in the code graph.

    Attributes:
        id: Unique identifier (e.g., "module.function_name")
        name: Display name
        node_type: Type of the node
        file_path: Source file path
        line_number: Line number in source file
        metadata: Additional metadata
    """

    id: str
    name: str
    node_type: NodeType
    file_path: str | None = None
    line_number: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "node_type": self.node_type.value,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "metadata": self.metadata,
        }


@dataclass
class GraphEdge:
    """Represents an edge in the code graph.

    Attributes:
        source: Source node ID
        target: Target node ID
        edge_type: Type of the relationship
        metadata: Additional metadata
    """

    source: str
    target: str
    edge_type: EdgeType
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "source": self.source,
            "target": self.target,
            "edge_type": self.edge_type.value,
            "metadata": self.metadata,
        }


@dataclass
class DependencyInfo:
    """Information about a code dependency.

    Attributes:
        module_name: The imported module name
        alias: Optional alias for the import
        is_relative: Whether it's a relative import
        level: Import level (0 for absolute, >0 for relative)
        imported_names: Specific names imported (for 'from X import Y')
        line_number: Line number of the import statement
    """

    module_name: str
    alias: str | None = None
    is_relative: bool = False
    level: int = 0
    imported_names: list[str] = field(default_factory=list)
    line_number: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "module_name": self.module_name,
            "alias": self.alias,
            "is_relative": self.is_relative,
            "level": self.level,
            "imported_names": self.imported_names,
            "line_number": self.line_number,
        }
