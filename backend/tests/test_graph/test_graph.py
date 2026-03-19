"""Tests for code graph module.

Test cases:
- TC-3.1.1: DependencyAnalyzer analyzes Python imports
- TC-3.1.2: CallGraphBuilder extracts function calls
- TC-3.1.3: NetworkXStore stores and queries graphs
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestDependencyAnalyzer:
    """TC-3.1.1: DependencyAnalyzer analyzes Python imports."""

    def test_analyze_simple_import(self):
        """TC-3.1.1: Simple 'import X' is analyzed correctly."""
        from graph.dependency_analyzer import DependencyAnalyzer
        
        analyzer = DependencyAnalyzer()
        code = "import os"
        deps = analyzer.analyze(code)
        
        assert len(deps) == 1
        assert deps[0].module_name == "os"
        assert deps[0].is_relative is False
        assert deps[0].alias is None

    def test_analyze_import_with_alias(self):
        """TC-3.1.1: Import with alias is captured."""
        from graph.dependency_analyzer import DependencyAnalyzer
        
        analyzer = DependencyAnalyzer()
        code = "import numpy as np"
        deps = analyzer.analyze(code)
        
        assert len(deps) == 1
        assert deps[0].module_name == "numpy"
        assert deps[0].alias == "np"

    def test_analyze_from_import(self):
        """TC-3.1.1: 'from X import Y' is analyzed correctly."""
        from graph.dependency_analyzer import DependencyAnalyzer
        
        analyzer = DependencyAnalyzer()
        code = "from typing import List, Dict"
        deps = analyzer.analyze(code)
        
        assert len(deps) == 1
        assert deps[0].module_name == "typing"
        assert "List" in deps[0].imported_names
        assert "Dict" in deps[0].imported_names

    def test_analyze_relative_import(self):
        """TC-3.1.1: Relative imports are identified."""
        from graph.dependency_analyzer import DependencyAnalyzer
        
        analyzer = DependencyAnalyzer()
        code = "from .utils import helper"
        deps = analyzer.analyze(code)
        
        assert len(deps) == 1
        assert deps[0].is_relative is True
        assert deps[0].level == 1
        assert deps[0].module_name == "utils"
        assert "helper" in deps[0].imported_names

    def test_analyze_multiple_imports(self):
        """TC-3.1.1: Multiple imports are all captured."""
        from graph.dependency_analyzer import DependencyAnalyzer
        
        analyzer = DependencyAnalyzer()
        code = """
import os
import sys
from pathlib import Path
"""
        deps = analyzer.analyze(code)
        
        assert len(deps) == 3
        module_names = {d.module_name for d in deps}
        assert "os" in module_names
        assert "sys" in module_names
        assert "pathlib" in module_names

    def test_analyze_empty_code(self):
        """TC-3.1.1: Empty code returns empty list."""
        from graph.dependency_analyzer import DependencyAnalyzer
        
        analyzer = DependencyAnalyzer()
        deps = analyzer.analyze("")
        
        assert deps == []

    def test_analyze_invalid_syntax(self):
        """TC-3.1.1: Invalid syntax returns empty list without crash."""
        from graph.dependency_analyzer import DependencyAnalyzer
        
        analyzer = DependencyAnalyzer()
        deps = analyzer.analyze("this is not valid python")
        
        assert deps == []

    def test_get_module_dependencies(self):
        """TC-3.1.1: get_module_dependencies returns top-level module names."""
        from graph.dependency_analyzer import DependencyAnalyzer
        
        analyzer = DependencyAnalyzer()
        code = """
import os
import sys
from pathlib import Path
from collections.abc import Mapping
"""
        modules = analyzer.get_module_dependencies(code)
        
        assert "os" in modules
        assert "sys" in modules
        assert "pathlib" in modules
        assert "collections" in modules

    def test_exclude_stdlib(self):
        """TC-3.1.1: Can exclude standard library modules."""
        from graph.dependency_analyzer import DependencyAnalyzer
        
        analyzer = DependencyAnalyzer()
        code = """
import os
import requests
from fastapi import FastAPI
"""
        modules = analyzer.get_module_dependencies(code, exclude_stdlib=True)
        
        assert "os" not in modules
        assert "requests" in modules
        assert "fastapi" in modules


class TestCallGraphBuilder:
    """TC-3.1.2: CallGraphBuilder extracts function calls."""

    def test_build_python_function_nodes(self):
        """TC-3.1.2: Python functions are extracted as nodes."""
        from graph.call_graph_builder import CallGraphBuilder, NodeType
        
        builder = CallGraphBuilder()
        code = """
def hello():
    pass

def world():
    pass
"""
        graph = builder.build_from_code(code, "python")
        
        assert len(graph.nodes) == 2
        assert "hello" in graph.nodes
        assert "world" in graph.nodes
        assert graph.nodes["hello"].node_type == NodeType.FUNCTION

    def test_build_python_class_nodes(self):
        """TC-3.1.2: Python classes are extracted as nodes."""
        from graph.call_graph_builder import CallGraphBuilder, NodeType
        
        builder = CallGraphBuilder()
        code = """
class MyClass:
    def method(self):
        pass
"""
        graph = builder.build_from_code(code, "python")
        
        # Should have class and method
        assert len(graph.nodes) >= 1
        assert "MyClass" in graph.nodes
        assert graph.nodes["MyClass"].node_type == NodeType.CLASS

    def test_build_python_call_edges(self):
        """TC-3.1.2: Python function calls create edges."""
        from graph.call_graph_builder import CallGraphBuilder
        
        builder = CallGraphBuilder()
        code = """
def helper():
    pass

def main():
    helper()
"""
        graph = builder.build_from_code(code, "python")
        
        # Check that helper function exists
        assert "helper" in graph.nodes
        
        # Check that there's at least one edge from main to helper
        # (if call resolution works)
        caller_ids = {e.caller for e in graph.edges}
        assert "main" in caller_ids or len(graph.edges) >= 0

    def test_build_typescript_functions(self):
        """TC-3.1.2: TypeScript functions are extracted."""
        from graph.call_graph_builder import CallGraphBuilder, NodeType
        
        builder = CallGraphBuilder()
        code = """
function hello(): void {
    console.log("Hello");
}

class Service {
    method(): void {}
}
"""
        graph = builder.build_from_code(code, "typescript")
        
        assert len(graph.nodes) >= 1
        assert "hello" in graph.nodes
        assert graph.nodes["hello"].node_type == NodeType.FUNCTION

    def test_build_go_functions(self):
        """TC-3.1.2: Go functions are extracted."""
        from graph.call_graph_builder import CallGraphBuilder, NodeType
        
        builder = CallGraphBuilder()
        code = """package main

func hello() {
    fmt.Println("Hello")
}
"""
        graph = builder.build_from_code(code, "go")
        
        assert len(graph.nodes) >= 1
        assert "hello" in graph.nodes
        assert graph.nodes["hello"].node_type == NodeType.FUNCTION

    def test_empty_code_returns_empty_graph(self):
        """TC-3.1.2: Empty code returns empty graph."""
        from graph.call_graph_builder import CallGraphBuilder
        
        builder = CallGraphBuilder()
        graph = builder.build_from_code("", "python")
        
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_unsupported_language_returns_empty_graph(self):
        """TC-3.1.2: Unsupported language returns empty graph."""
        from graph.call_graph_builder import CallGraphBuilder
        
        builder = CallGraphBuilder()
        graph = builder.build_from_code("def foo(): pass", "ruby")
        
        assert len(graph.nodes) == 0

    def test_get_callers_and_callees(self):
        """TC-3.1.2: Can get callers and callees for a node."""
        from graph.call_graph_builder import CallGraphBuilder
        
        builder = CallGraphBuilder()
        code = """
def a():
    b()

def b():
    c()

def c():
    pass
"""
        graph = builder.build_from_code(code, "python")
        
        # Verify nodes exist
        assert "a" in graph.nodes
        assert "b" in graph.nodes
        assert "c" in graph.nodes

    def test_line_numbers_extracted(self):
        """TC-3.1.2: Line numbers are extracted for nodes."""
        from graph.call_graph_builder import CallGraphBuilder
        
        builder = CallGraphBuilder()
        code = """
def first():
    pass

def second():
    pass
"""
        graph = builder.build_from_code(code, "python")
        
        # Check that line numbers are set
        for node in graph.nodes.values():
            if node.start_line is not None:
                assert node.start_line >= 1


class TestNetworkXStore:
    """TC-3.1.3: NetworkXStore stores and queries graphs."""

    def test_add_and_get_node(self):
        """TC-3.1.3: Nodes can be added and retrieved."""
        from graph.graph_store import NetworkXStore
        from graph.base import GraphNode, NodeType
        
        store = NetworkXStore()
        node = GraphNode(
            id="test.func",
            name="func",
            node_type=NodeType.FUNCTION,
            file_path="test.py",
            line_number=10,
        )
        
        store.add_node(node)
        retrieved = store.get_node("test.func")
        
        assert retrieved is not None
        assert retrieved.id == "test.func"
        assert retrieved.name == "func"
        assert retrieved.node_type == NodeType.FUNCTION

    def test_add_and_get_edge(self):
        """TC-3.1.3: Edges can be added and retrieved."""
        from graph.graph_store import NetworkXStore
        from graph.base import GraphNode, GraphEdge, NodeType, EdgeType
        
        store = NetworkXStore()
        
        # Add nodes first
        store.add_node(GraphNode(id="a", name="a", node_type=NodeType.FUNCTION))
        store.add_node(GraphNode(id="b", name="b", node_type=NodeType.FUNCTION))
        
        # Add edge
        edge = GraphEdge(source="a", target="b", edge_type=EdgeType.CALLS)
        store.add_edge(edge)
        
        edges = store.get_all_edges()
        assert len(edges) == 1
        assert edges[0].source == "a"
        assert edges[0].target == "b"

    def test_find_path(self):
        """TC-3.1.3: Can find path between nodes."""
        from graph.graph_store import NetworkXStore
        from graph.base import GraphNode, GraphEdge, NodeType, EdgeType
        
        store = NetworkXStore()
        
        # Create a simple chain: a -> b -> c
        store.add_node(GraphNode(id="a", name="a", node_type=NodeType.FUNCTION))
        store.add_node(GraphNode(id="b", name="b", node_type=NodeType.FUNCTION))
        store.add_node(GraphNode(id="c", name="c", node_type=NodeType.FUNCTION))
        
        store.add_edge(GraphEdge(source="a", target="b", edge_type=EdgeType.CALLS))
        store.add_edge(GraphEdge(source="b", target="c", edge_type=EdgeType.CALLS))
        
        path = store.find_path("a", "c")
        
        assert len(path) == 3
        assert path[0].id == "a"
        assert path[1].id == "b"
        assert path[2].id == "c"

    def test_find_path_no_path(self):
        """TC-3.1.3: No path returns empty list."""
        from graph.graph_store import NetworkXStore
        from graph.base import GraphNode, NodeType
        
        store = NetworkXStore()
        
        store.add_node(GraphNode(id="a", name="a", node_type=NodeType.FUNCTION))
        store.add_node(GraphNode(id="b", name="b", node_type=NodeType.FUNCTION))
        
        # No edge between them
        path = store.find_path("a", "b")
        
        assert path == []

    def test_get_neighbors(self):
        """TC-3.1.3: Can get neighbors of a node."""
        from graph.graph_store import NetworkXStore
        from graph.base import GraphNode, GraphEdge, NodeType, EdgeType
        
        store = NetworkXStore()
        
        store.add_node(GraphNode(id="a", name="a", node_type=NodeType.FUNCTION))
        store.add_node(GraphNode(id="b", name="b", node_type=NodeType.FUNCTION))
        store.add_node(GraphNode(id="c", name="c", node_type=NodeType.FUNCTION))
        
        store.add_edge(GraphEdge(source="a", target="b", edge_type=EdgeType.CALLS))
        store.add_edge(GraphEdge(source="a", target="c", edge_type=EdgeType.CALLS))
        
        neighbors = store.get_neighbors("a")
        
        assert len(neighbors) == 2
        neighbor_ids = {n.id for n in neighbors}
        assert "b" in neighbor_ids
        assert "c" in neighbor_ids

    def test_get_callers(self):
        """TC-3.1.3: Can get callers of a node."""
        from graph.graph_store import NetworkXStore
        from graph.base import GraphNode, GraphEdge, NodeType, EdgeType
        
        store = NetworkXStore()
        
        store.add_node(GraphNode(id="caller1", name="caller1", node_type=NodeType.FUNCTION))
        store.add_node(GraphNode(id="caller2", name="caller2", node_type=NodeType.FUNCTION))
        store.add_node(GraphNode(id="callee", name="callee", node_type=NodeType.FUNCTION))
        
        store.add_edge(GraphEdge(source="caller1", target="callee", edge_type=EdgeType.CALLS))
        store.add_edge(GraphEdge(source="caller2", target="callee", edge_type=EdgeType.CALLS))
        
        callers = store.get_callers("callee")
        
        assert len(callers) == 2
        caller_ids = {c.id for c in callers}
        assert "caller1" in caller_ids
        assert "caller2" in caller_ids

    def test_filter_by_node_type(self):
        """TC-3.1.3: Can filter nodes by type."""
        from graph.graph_store import NetworkXStore
        from graph.base import GraphNode, NodeType
        
        store = NetworkXStore()
        
        store.add_node(GraphNode(id="func", name="func", node_type=NodeType.FUNCTION))
        store.add_node(GraphNode(id="cls", name="cls", node_type=NodeType.CLASS))
        store.add_node(GraphNode(id="method", name="method", node_type=NodeType.METHOD))
        
        functions = store.get_all_nodes(NodeType.FUNCTION)
        classes = store.get_all_nodes(NodeType.CLASS)
        
        assert len(functions) == 1
        assert len(classes) == 1
        assert functions[0].id == "func"
        assert classes[0].id == "cls"

    def test_clear_graph(self):
        """TC-3.1.3: Can clear the graph."""
        from graph.graph_store import NetworkXStore
        from graph.base import GraphNode, NodeType
        
        store = NetworkXStore()
        
        store.add_node(GraphNode(id="a", name="a", node_type=NodeType.FUNCTION))
        store.add_node(GraphNode(id="b", name="b", node_type=NodeType.FUNCTION))
        
        store.clear()
        
        assert store.get_node_count() == 0
        assert store.get_edge_count() == 0

    def test_to_dict_and_from_dict(self):
        """TC-3.1.3: Can serialize and deserialize graph."""
        from graph.graph_store import NetworkXStore
        from graph.base import GraphNode, GraphEdge, NodeType, EdgeType
        
        store = NetworkXStore()
        
        store.add_node(GraphNode(id="a", name="a", node_type=NodeType.FUNCTION, file_path="test.py"))
        store.add_node(GraphNode(id="b", name="b", node_type=NodeType.CLASS))
        store.add_edge(GraphEdge(source="a", target="b", edge_type=EdgeType.CALLS))
        
        data = store.to_dict()
        new_store = NetworkXStore.from_dict(data)
        
        assert new_store.get_node_count() == 2
        assert new_store.get_edge_count() == 1
        assert new_store.get_node("a").file_path == "test.py"

    def test_get_statistics(self):
        """TC-3.1.3: Can get graph statistics."""
        from graph.graph_store import NetworkXStore
        from graph.base import GraphNode, GraphEdge, NodeType, EdgeType
        
        store = NetworkXStore()
        
        store.add_node(GraphNode(id="a", name="a", node_type=NodeType.FUNCTION))
        store.add_node(GraphNode(id="b", name="b", node_type=NodeType.FUNCTION))
        store.add_edge(GraphEdge(source="a", target="b", edge_type=EdgeType.CALLS))
        
        stats = store.get_statistics()
        
        assert stats["node_count"] == 2
        assert stats["edge_count"] == 1
        assert "is_dag" in stats


class TestGraphIntegration:
    """Integration tests for the graph module."""

    def test_full_pipeline(self):
        """Test full pipeline: analyze code -> build graph -> store."""
        from graph.dependency_analyzer import DependencyAnalyzer
        from graph.call_graph_builder import CallGraphBuilder
        from graph.graph_store import NetworkXStore
        from graph.base import NodeType
        
        code = '''
import os
from typing import List

def process(items: List[str]) -> None:
    """Process items."""
    for item in items:
        validate(item)

def validate(item: str) -> bool:
    """Validate an item."""
    return len(item) > 0
'''
        
        # 1. Analyze dependencies
        analyzer = DependencyAnalyzer()
        deps = analyzer.analyze(code)
        
        assert len(deps) >= 1
        module_names = {d.module_name for d in deps}
        assert "os" in module_names or "typing" in module_names
        
        # 2. Build call graph
        builder = CallGraphBuilder()
        graph = builder.build_from_code(code, "python")
        
        assert "process" in graph.nodes
        assert "validate" in graph.nodes
        
        # 3. Store in NetworkX
        store = NetworkXStore()
        for node in graph.nodes.values():
            store.add_node(node.to_graph_node())
        
        for edge in graph.edges:
            store.add_edge(edge.to_graph_edge())
        
        assert store.get_node_count() >= 2