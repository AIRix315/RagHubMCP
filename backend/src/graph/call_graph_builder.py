"""Call graph builder for extracting function call relationships.

Uses tree-sitter to parse code and extract function call relationships
for building call graphs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.graph.base import EdgeType, GraphEdge, GraphNode, NodeType

logger = logging.getLogger(__name__)

# Lazy imports for tree-sitter
_ts_python: Any = None
_ts_typescript: Any = None
_ts_go: Any = None


def _get_tree_sitter_python() -> Any:
    """Lazily import tree-sitter-python."""
    global _ts_python
    if _ts_python is None:
        import tree_sitter_python

        _ts_python = tree_sitter_python
    return _ts_python


def _get_tree_sitter_typescript() -> Any:
    """Lazily import tree-sitter-typescript."""
    global _ts_typescript
    if _ts_typescript is None:
        import tree_sitter_typescript

        _ts_typescript = tree_sitter_typescript
    return _ts_typescript


def _get_tree_sitter_go() -> Any:
    """Lazily import tree-sitter-go."""
    global _ts_go
    if _ts_go is None:
        import tree_sitter_go

        _ts_go = tree_sitter_go
    return _ts_go


@dataclass
class CallNode:
    """Represents a callable unit (function/method/class) in the call graph.

    Attributes:
        id: Unique identifier (e.g., "module.ClassName.method_name")
        name: Simple name (e.g., "method_name")
        full_name: Fully qualified name
        node_type: Type of callable (function, method, class)
        file_path: Source file path
        start_line: Starting line number
        end_line: Ending line number
        metadata: Additional metadata
    """

    id: str
    name: str
    full_name: str
    node_type: NodeType
    file_path: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_graph_node(self) -> GraphNode:
        """Convert to GraphNode."""
        return GraphNode(
            id=self.id,
            name=self.name,
            node_type=self.node_type,
            file_path=self.file_path,
            line_number=self.start_line,
            metadata={
                "full_name": self.full_name,
                "end_line": self.end_line,
                **self.metadata,
            },
        )


@dataclass
class CallEdge:
    """Represents a call relationship between two callables.

    Attributes:
        caller: ID of the calling function/method
        callee: ID of the called function/method
        call_site_line: Line number where the call occurs
        metadata: Additional metadata
    """

    caller: str
    callee: str
    call_site_line: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_graph_edge(self) -> GraphEdge:
        """Convert to GraphEdge."""
        return GraphEdge(
            source=self.caller,
            target=self.callee,
            edge_type=EdgeType.CALLS,
            metadata={
                "call_site_line": self.call_site_line,
                **self.metadata,
            },
        )


@dataclass
class CallGraph:
    """Represents a complete call graph for a codebase.

    Attributes:
        nodes: Dictionary of node ID to CallNode
        edges: List of CallEdge objects
        file_path: Source file path this graph represents
    """

    nodes: dict[str, CallNode] = field(default_factory=dict)
    edges: list[CallEdge] = field(default_factory=list)
    file_path: str | None = None

    def add_node(self, node: CallNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node

    def add_edge(self, edge: CallEdge) -> None:
        """Add an edge to the graph."""
        self.edges.append(edge)

    def get_callers(self, callee_id: str) -> list[CallNode]:
        """Get all nodes that call the given node."""
        caller_ids = {e.caller for e in self.edges if e.callee == callee_id}
        return [self.nodes[cid] for cid in caller_ids if cid in self.nodes]

    def get_callees(self, caller_id: str) -> list[CallNode]:
        """Get all nodes called by the given node."""
        callee_ids = {e.callee for e in self.edges if e.caller == caller_id}
        return [self.nodes[cid] for cid in callee_ids if cid in self.nodes]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "nodes": {nid: node.__dict__ for nid, node in self.nodes.items()},
            "edges": [edge.__dict__ for edge in self.edges],
            "file_path": self.file_path,
        }


class CallGraphBuilder:
    """Builds call graphs from source code using tree-sitter.

    Supports Python, TypeScript, and Go languages.

    Example:
        >>> builder = CallGraphBuilder()
        >>> graph = builder.build_from_code(code, "python", "module.py")
        >>> len(graph.nodes)
        2
    """

    NAME = "call-graph-builder"
    SUPPORTED_LANGUAGES = ["python", "typescript", "go"]

    def build_from_code(
        self, source_code: str, language: str, file_path: str | None = None
    ) -> CallGraph:
        """Build a call graph from source code.

        Args:
            source_code: Source code to analyze
            language: Language of the source code (python, typescript, go)
            file_path: Optional file path for context

        Returns:
            CallGraph containing nodes and edges
        """
        if not source_code or not source_code.strip():
            return CallGraph(file_path=file_path)

        language = language.lower()

        if language in ("python", "py"):
            return self._build_python_call_graph(source_code, file_path)
        elif language in ("typescript", "ts", "tsx"):
            return self._build_typescript_call_graph(source_code, file_path)
        elif language in ("go", "golang"):
            return self._build_go_call_graph(source_code, file_path)
        else:
            logger.warning(f"Unsupported language: {language}")
            return CallGraph(file_path=file_path)

    def build_from_file(self, file_path: str | Path) -> CallGraph:
        """Build a call graph from a source file.

        Args:
            file_path: Path to the source file

        Returns:
            CallGraph containing nodes and edges
        """
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"File not found: {file_path}")
            return CallGraph(file_path=str(path))

        # Detect language from extension
        ext = path.suffix.lower()
        language_map = {
            ".py": "python",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".go": "go",
        }
        language = language_map.get(ext)
        if not language:
            logger.warning(f"Unknown file extension: {ext}")
            return CallGraph(file_path=str(path))

        try:
            source_code = path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Error reading file {file_path}: {e}")
            return CallGraph(file_path=str(path))

        return self.build_from_code(source_code, language, str(path))

    def _build_python_call_graph(self, source_code: str, file_path: str | None) -> CallGraph:
        """Build call graph for Python code using tree-sitter."""
        graph = CallGraph(file_path=file_path)

        try:
            from tree_sitter import Language, Parser

            ts_python = _get_tree_sitter_python()
            language = Language(ts_python.language())
            parser = Parser(language)
            tree = parser.parse(bytes(source_code, "utf-8"))

            # First pass: collect all function/class definitions
            self._collect_python_definitions(tree.root_node, source_code, graph)

            # Second pass: collect function calls
            self._collect_python_calls(tree.root_node, source_code, graph)

        except ImportError:
            logger.warning("tree-sitter-python not installed")
        except Exception as e:
            logger.warning(f"Error parsing Python: {e}")

        return graph

    def _collect_python_definitions(
        self, node: Any, source: str, graph: CallGraph, class_context: str | None = None
    ) -> None:
        """Collect function and class definitions from Python AST."""
        _ = source.encode("utf-8")  # Unused, kept for potential future use

        if node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = name_node.text.decode("utf-8")
                if class_context:
                    full_name = f"{class_context}.{name}"
                    node_type = NodeType.METHOD
                else:
                    full_name = name
                    node_type = NodeType.FUNCTION

                node_id = full_name
                graph.add_node(
                    CallNode(
                        id=node_id,
                        name=name,
                        full_name=full_name,
                        node_type=node_type,
                        file_path=graph.file_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        metadata={"class_context": class_context},
                    )
                )

        elif node.type == "class_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = name_node.text.decode("utf-8")
                full_name = name
                graph.add_node(
                    CallNode(
                        id=full_name,
                        name=name,
                        full_name=full_name,
                        node_type=NodeType.CLASS,
                        file_path=graph.file_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                    )
                )

                # Process class methods with class context
                for child in node.children:
                    if child.type == "block":
                        for block_child in child.children:
                            self._collect_python_definitions(
                                block_child, source, graph, class_context=name
                            )
                return

        # Recurse into children
        for child in node.children:
            self._collect_python_definitions(child, source, graph, class_context)

    def _collect_python_calls(
        self, node: Any, source: str, graph: CallGraph, current_function: str | None = None
    ) -> None:
        """Collect function calls from Python AST."""
        if node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                current_function = name_node.text.decode("utf-8")

        if node.type == "call" and current_function:
            # Get the function being called
            func_node = node.child_by_field_name("function")
            if func_node:
                callee_name = func_node.text.decode("utf-8")

                # Handle method calls (self.method, obj.method)
                if "." in callee_name:
                    parts = callee_name.split(".")
                    callee_name = parts[-1]  # Just the method name

                # Only record if callee exists in graph
                if callee_name in graph.nodes:
                    graph.add_edge(
                        CallEdge(
                            caller=current_function,
                            callee=callee_name,
                            call_site_line=node.start_point[0] + 1,
                        )
                    )

        # Recurse into children
        for child in node.children:
            self._collect_python_calls(child, source, graph, current_function)

    def _build_typescript_call_graph(self, source_code: str, file_path: str | None) -> CallGraph:
        """Build call graph for TypeScript code."""
        graph = CallGraph(file_path=file_path)

        try:
            import tree_sitter_typescript
            from tree_sitter import Language, Parser

            language = Language(tree_sitter_typescript.language_typescript())
            parser = Parser(language)
            tree = parser.parse(bytes(source_code, "utf-8"))

            self._collect_typescript_definitions(tree.root_node, source_code, graph)
            self._collect_typescript_calls(tree.root_node, source_code, graph)

        except ImportError:
            logger.warning("tree-sitter-typescript not installed")
        except Exception as e:
            logger.warning(f"Error parsing TypeScript: {e}")

        return graph

    def _collect_typescript_definitions(
        self, node: Any, source: str, graph: CallGraph, class_context: str | None = None
    ) -> None:
        """Collect TypeScript definitions."""
        # Similar structure to Python, but with TypeScript node types
        if node.type == "function_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = name_node.text.decode("utf-8")
                full_name = f"{class_context}.{name}" if class_context else name
                graph.add_node(
                    CallNode(
                        id=full_name,
                        name=name,
                        full_name=full_name,
                        node_type=NodeType.FUNCTION,
                        file_path=graph.file_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                    )
                )

        elif node.type == "class_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = name_node.text.decode("utf-8")
                graph.add_node(
                    CallNode(
                        id=name,
                        name=name,
                        full_name=name,
                        node_type=NodeType.CLASS,
                        file_path=graph.file_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                    )
                )
                class_context = name

        elif node.type == "method_definition":
            name_node = node.child_by_field_name("name")
            if name_node and class_context:
                name = name_node.text.decode("utf-8")
                full_name = f"{class_context}.{name}"
                graph.add_node(
                    CallNode(
                        id=full_name,
                        name=name,
                        full_name=full_name,
                        node_type=NodeType.METHOD,
                        file_path=graph.file_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        metadata={"class_context": class_context},
                    )
                )

        for child in node.children:
            self._collect_typescript_definitions(child, source, graph, class_context)

    def _collect_typescript_calls(
        self, node: Any, source: str, graph: CallGraph, current_function: str | None = None
    ) -> None:
        """Collect TypeScript calls."""
        # Track current function context
        if node.type in ("function_declaration", "method_definition"):
            name_node = node.child_by_field_name("name")
            if name_node:
                current_function = name_node.text.decode("utf-8")

        if node.type == "call_expression" and current_function:
            func_node = node.child_by_field_name("function")
            if func_node:
                callee_name = func_node.text.decode("utf-8")
                # Simplify callee name
                if "." in callee_name:
                    callee_name = callee_name.split(".")[-1]

                if callee_name in graph.nodes:
                    graph.add_edge(
                        CallEdge(
                            caller=current_function,
                            callee=callee_name,
                            call_site_line=node.start_point[0] + 1,
                        )
                    )

        for child in node.children:
            self._collect_typescript_calls(child, source, graph, current_function)

    def _build_go_call_graph(self, source_code: str, file_path: str | None) -> CallGraph:
        """Build call graph for Go code."""
        graph = CallGraph(file_path=file_path)

        try:
            from tree_sitter import Language, Parser

            ts_go = _get_tree_sitter_go()
            language = Language(ts_go.language())
            parser = Parser(language)
            tree = parser.parse(bytes(source_code, "utf-8"))

            self._collect_go_definitions(tree.root_node, source_code, graph)
            self._collect_go_calls(tree.root_node, source_code, graph)

        except ImportError:
            logger.warning("tree-sitter-go not installed")
        except Exception as e:
            logger.warning(f"Error parsing Go: {e}")

        return graph

    def _collect_go_definitions(
        self, node: Any, source: str, graph: CallGraph, receiver_type: str | None = None
    ) -> None:
        """Collect Go function and type definitions."""
        if node.type == "function_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = name_node.text.decode("utf-8")
                full_name = f"{receiver_type}.{name}" if receiver_type else name
                graph.add_node(
                    CallNode(
                        id=full_name,
                        name=name,
                        full_name=full_name,
                        node_type=NodeType.METHOD if receiver_type else NodeType.FUNCTION,
                        file_path=graph.file_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        metadata={"receiver_type": receiver_type},
                    )
                )

        elif node.type == "method_declaration":
            # Go method with receiver
            name_node = node.child_by_field_name("name")
            receiver_node = node.child_by_field_name("receiver")
            if name_node:
                name = name_node.text.decode("utf-8")
                # Extract receiver type
                recv_type = None
                if receiver_node:
                    # Simplified receiver type extraction
                    recv_type = "receiver"  # Placeholder
                full_name = f"{recv_type}.{name}" if recv_type else name
                graph.add_node(
                    CallNode(
                        id=full_name,
                        name=name,
                        full_name=full_name,
                        node_type=NodeType.METHOD,
                        file_path=graph.file_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        metadata={"receiver_type": recv_type},
                    )
                )

        elif node.type == "type_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                name = name_node.text.decode("utf-8")
                graph.add_node(
                    CallNode(
                        id=name,
                        name=name,
                        full_name=name,
                        node_type=NodeType.CLASS,  # Go type
                        file_path=graph.file_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                    )
                )

        for child in node.children:
            self._collect_go_definitions(child, source, graph, receiver_type)

    def _collect_go_calls(
        self, node: Any, source: str, graph: CallGraph, current_function: str | None = None
    ) -> None:
        """Collect Go function calls."""
        if node.type in ("function_declaration", "method_declaration"):
            name_node = node.child_by_field_name("name")
            if name_node:
                current_function = name_node.text.decode("utf-8")

        if node.type == "call_expression" and current_function:
            func_node = node.child_by_field_name("function")
            if func_node:
                callee_name = func_node.text.decode("utf-8")
                # Simplify
                if "." in callee_name:
                    callee_name = callee_name.split(".")[-1]

                if callee_name in graph.nodes:
                    graph.add_edge(
                        CallEdge(
                            caller=current_function,
                            callee=callee_name,
                            call_site_line=node.start_point[0] + 1,
                        )
                    )

        for child in node.children:
            self._collect_go_calls(child, source, graph, current_function)
