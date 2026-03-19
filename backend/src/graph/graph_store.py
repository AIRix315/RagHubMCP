"""Graph storage backends for code graphs.

Provides abstract interface and implementations for storing and querying
code dependency and call graphs using NetworkX (in-memory) or Neo4j.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from src.graph.base import GraphNode, GraphEdge, NodeType, EdgeType

logger = logging.getLogger(__name__)

# Check if NetworkX is available
_NETWORKX_AVAILABLE = False
try:
    import networkx as nx
    _NETWORKX_AVAILABLE = True
except ImportError:
    pass

# Check if Neo4j driver is available
_NEO4J_AVAILABLE = False
try:
    from neo4j import GraphDatabase
    _NEO4J_AVAILABLE = True
except ImportError:
    pass


class GraphStore(ABC):
    """Abstract base class for graph storage backends.
    
    Defines the interface for storing and querying code graphs.
    Implementations can use NetworkX (in-memory) or Neo4j (persistent).
    """
    
    @abstractmethod
    def add_node(self, node: GraphNode) -> None:
        """Add a node to the graph.
        
        Args:
            node: The node to add
        """
        ...
    
    @abstractmethod
    def add_edge(self, edge: GraphEdge) -> None:
        """Add an edge to the graph.
        
        Args:
            edge: The edge to add
        """
        ...
    
    @abstractmethod
    def get_node(self, node_id: str) -> GraphNode | None:
        """Get a node by ID.
        
        Args:
            node_id: The node identifier
            
        Returns:
            The node or None if not found
        """
        ...
    
    @abstractmethod
    def get_neighbors(self, node_id: str, edge_type: EdgeType | None = None) -> list[GraphNode]:
        """Get neighbors of a node.
        
        Args:
            node_id: The node identifier
            edge_type: Optional filter by edge type
            
        Returns:
            List of neighboring nodes
        """
        ...
    
    @abstractmethod
    def find_path(self, source_id: str, target_id: str) -> list[GraphNode]:
        """Find a path between two nodes.
        
        Args:
            source_id: Starting node ID
            target_id: Target node ID
            
        Returns:
            List of nodes forming a path (empty if no path exists)
        """
        ...
    
    @abstractmethod
    def get_all_nodes(self, node_type: NodeType | None = None) -> list[GraphNode]:
        """Get all nodes, optionally filtered by type.
        
        Args:
            node_type: Optional filter by node type
            
        Returns:
            List of all matching nodes
        """
        ...
    
    @abstractmethod
    def get_all_edges(self, edge_type: EdgeType | None = None) -> list[GraphEdge]:
        """Get all edges, optionally filtered by type.
        
        Args:
            edge_type: Optional filter by edge type
            
        Returns:
            List of all matching edges
        """
        ...
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all nodes and edges from the graph."""
        ...
    
    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Export the graph to a dictionary.
        
        Returns:
            Dictionary representation of the graph
        """
        ...
    
    @classmethod
    def is_networkx_available(cls) -> bool:
        """Check if NetworkX is available."""
        return _NETWORKX_AVAILABLE
    
    @classmethod
    def is_neo4j_available(cls) -> bool:
        """Check if Neo4j driver is available."""
        return _NEO4J_AVAILABLE


class NetworkXStore(GraphStore):
    """In-memory graph storage using NetworkX.
    
    Suitable for small to medium graphs that fit in memory.
    Provides fast traversal and path finding algorithms.
    
    Example:
        >>> store = NetworkXStore()
        >>> store.add_node(GraphNode(id="main", name="main", node_type=NodeType.FUNCTION))
        >>> node = store.get_node("main")
        >>> node.name
        'main'
    """
    
    def __init__(self) -> None:
        """Initialize an empty NetworkX directed graph."""
        if not _NETWORKX_AVAILABLE:
            raise ImportError("NetworkX is not installed. Install with: pip install networkx")
        
        self._graph: nx.DiGraph = nx.DiGraph()
        self._nodes: dict[str, GraphNode] = {}
        self._edges: list[GraphEdge] = []
    
    def add_node(self, node: GraphNode) -> None:
        """Add a node to the graph."""
        self._nodes[node.id] = node
        self._graph.add_node(node.id, **node.to_dict())
    
    def add_edge(self, edge: GraphEdge) -> None:
        """Add an edge to the graph."""
        self._edges.append(edge)
        self._graph.add_edge(
            edge.source, 
            edge.target, 
            edge_type=edge.edge_type.value,
            **edge.metadata
        )
    
    def get_node(self, node_id: str) -> GraphNode | None:
        """Get a node by ID."""
        return self._nodes.get(node_id)
    
    def get_neighbors(self, node_id: str, edge_type: EdgeType | None = None) -> list[GraphNode]:
        """Get neighbors of a node."""
        if node_id not in self._graph:
            return []
        
        neighbors = []
        for neighbor_id in self._graph.successors(node_id):
            edge_data = self._graph.get_edge_data(node_id, neighbor_id)
            if edge_type is None or edge_data.get("edge_type") == edge_type.value:
                neighbor = self._nodes.get(neighbor_id)
                if neighbor:
                    neighbors.append(neighbor)
        
        return neighbors
    
    def find_path(self, source_id: str, target_id: str) -> list[GraphNode]:
        """Find the shortest path between two nodes."""
        if source_id not in self._graph or target_id not in self._graph:
            return []
        
        try:
            path = nx.shortest_path(self._graph, source_id, target_id)
            return [self._nodes[nid] for nid in path if nid in self._nodes]
        except nx.NetworkXNoPath:
            return []
    
    def find_all_paths(self, source_id: str, target_id: str, cutoff: int | None = None) -> list[list[GraphNode]]:
        """Find all paths between two nodes.
        
        Args:
            source_id: Starting node ID
            target_id: Target node ID
            cutoff: Maximum path length
            
        Returns:
            List of paths (each path is a list of nodes)
        """
        if source_id not in self._graph or target_id not in self._graph:
            return []
        
        try:
            paths = nx.all_simple_paths(self._graph, source_id, target_id, cutoff=cutoff)
            return [
                [self._nodes[nid] for nid in path if nid in self._nodes]
                for path in paths
            ]
        except nx.NetworkXNoPath:
            return []
    
    def get_callers(self, node_id: str) -> list[GraphNode]:
        """Get all nodes that call the given node (predecessors in call graph)."""
        if node_id not in self._graph:
            return []
        
        callers = []
        for caller_id in self._graph.predecessors(node_id):
            edge_data = self._graph.get_edge_data(caller_id, node_id)
            if edge_data.get("edge_type") == EdgeType.CALLS.value:
                caller = self._nodes.get(caller_id)
                if caller:
                    callers.append(caller)
        
        return callers
    
    def get_callees(self, node_id: str) -> list[GraphNode]:
        """Get all nodes called by the given node (successors in call graph)."""
        return self.get_neighbors(node_id, EdgeType.CALLS)
    
    def get_all_nodes(self, node_type: NodeType | None = None) -> list[GraphNode]:
        """Get all nodes, optionally filtered by type."""
        if node_type is None:
            return list(self._nodes.values())
        
        return [
            node for node in self._nodes.values()
            if node.node_type == node_type
        ]
    
    def get_all_edges(self, edge_type: EdgeType | None = None) -> list[GraphEdge]:
        """Get all edges, optionally filtered by type."""
        if edge_type is None:
            return list(self._edges)
        
        return [
            edge for edge in self._edges
            if edge.edge_type == edge_type
        ]
    
    def get_node_count(self) -> int:
        """Get the total number of nodes."""
        return self._graph.number_of_nodes()
    
    def get_edge_count(self) -> int:
        """Get the total number of edges."""
        return self._graph.number_of_edges()
    
    def get_statistics(self) -> dict[str, Any]:
        """Get graph statistics."""
        return {
            "node_count": self._graph.number_of_nodes(),
            "edge_count": self._graph.number_of_edges(),
            "is_dag": nx.is_directed_acyclic_graph(self._graph) if self._graph.number_of_nodes() > 0 else True,
            "strongly_connected_components": nx.number_strongly_connected_components(self._graph) if self._graph.number_of_nodes() > 0 else 0,
        }
    
    def clear(self) -> None:
        """Clear all nodes and edges."""
        self._graph.clear()
        self._nodes.clear()
        self._edges.clear()
    
    def to_dict(self) -> dict[str, Any]:
        """Export the graph to a dictionary."""
        return {
            "nodes": [node.to_dict() for node in self._nodes.values()],
            "edges": [edge.to_dict() for edge in self._edges],
            "statistics": self.get_statistics(),
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NetworkXStore":
        """Create a NetworkXStore from a dictionary.
        
        Args:
            data: Dictionary representation of the graph
            
        Returns:
            A new NetworkXStore instance
        """
        store = cls()
        
        for node_data in data.get("nodes", []):
            node = GraphNode(
                id=node_data["id"],
                name=node_data["name"],
                node_type=NodeType(node_data["node_type"]),
                file_path=node_data.get("file_path"),
                line_number=node_data.get("line_number"),
                metadata=node_data.get("metadata", {}),
            )
            store.add_node(node)
        
        for edge_data in data.get("edges", []):
            edge = GraphEdge(
                source=edge_data["source"],
                target=edge_data["target"],
                edge_type=EdgeType(edge_data["edge_type"]),
                metadata=edge_data.get("metadata", {}),
            )
            store.add_edge(edge)
        
        return store
    
    def save_to_file(self, file_path: str | Path) -> None:
        """Save the graph to a file (JSON format).
        
        Args:
            file_path: Path to save the graph
        """
        import json
        
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
    
    @classmethod
    def load_from_file(cls, file_path: str | Path) -> "NetworkXStore":
        """Load a graph from a file.
        
        Args:
            file_path: Path to load the graph from
            
        Returns:
            A new NetworkXStore instance
        """
        import json
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return cls.from_dict(data)


class Neo4jStore(GraphStore):
    """Persistent graph storage using Neo4j.
    
    Suitable for large graphs that need persistence and complex queries.
    Requires a running Neo4j database.
    
    Example:
        >>> store = Neo4jStore("bolt://localhost:7687", ("neo4j", "password"))
        >>> store.add_node(GraphNode(id="main", name="main", node_type=NodeType.FUNCTION))
    """
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        auth: tuple[str, str] = ("neo4j", "password"),
        database: str = "neo4j",
    ) -> None:
        """Initialize connection to Neo4j database.
        
        Args:
            uri: Neo4j connection URI
            auth: (username, password) tuple
            database: Database name
        """
        if not _NEO4J_AVAILABLE:
            raise ImportError("Neo4j driver is not installed. Install with: pip install neo4j")
        
        self._uri = uri
        self._auth = auth
        self._database = database
        self._driver = GraphDatabase.driver(uri, auth=auth)
    
    def close(self) -> None:
        """Close the database connection."""
        self._driver.close()
    
    def __enter__(self) -> "Neo4jStore":
        return self
    
    def __exit__(self, *args: Any) -> None:
        self.close()
    
    def add_node(self, node: GraphNode) -> None:
        """Add a node to the graph."""
        query = """
        MERGE (n:CodeNode {id: $id})
        SET n.name = $name,
            n.node_type = $node_type,
            n.file_path = $file_path,
            n.line_number = $line_number
        SET n += $metadata
        """
        
        with self._driver.session(database=self._database) as session:
            session.run(
                query,
                id=node.id,
                name=node.name,
                node_type=node.node_type.value,
                file_path=node.file_path,
                line_number=node.line_number,
                metadata=node.metadata,
            )
    
    def add_edge(self, edge: GraphEdge) -> None:
        """Add an edge to the graph."""
        query = """
        MATCH (source:CodeNode {id: $source_id})
        MATCH (target:CodeNode {id: $target_id})
        MERGE (source)-[r:RELATIONSHIP {edge_type: $edge_type}]->(target)
        SET r += $metadata
        """
        
        with self._driver.session(database=self._database) as session:
            session.run(
                query,
                source_id=edge.source,
                target_id=edge.target,
                edge_type=edge.edge_type.value,
                metadata=edge.metadata,
            )
    
    def get_node(self, node_id: str) -> GraphNode | None:
        """Get a node by ID."""
        query = """
        MATCH (n:CodeNode {id: $id})
        RETURN n.id, n.name, n.node_type, n.file_path, n.line_number, properties(n) as props
        """
        
        with self._driver.session(database=self._database) as session:
            result = session.run(query, id=node_id)
            record = result.single()
            
            if record:
                props = dict(record["props"])
                # Remove already extracted properties
                for key in ["id", "name", "node_type", "file_path", "line_number"]:
                    props.pop(key, None)
                
                return GraphNode(
                    id=record["n.id"],
                    name=record["n.name"],
                    node_type=NodeType(record["n.node_type"]),
                    file_path=record["n.file_path"],
                    line_number=record["n.line_number"],
                    metadata=props,
                )
        
        return None
    
    def get_neighbors(self, node_id: str, edge_type: EdgeType | None = None) -> list[GraphNode]:
        """Get neighbors of a node."""
        if edge_type:
            query = """
            MATCH (n:CodeNode {id: $id})-[:RELATIONSHIP {edge_type: $edge_type}]->(neighbor:CodeNode)
            RETURN neighbor.id, neighbor.name, neighbor.node_type, neighbor.file_path, 
                   neighbor.line_number, properties(neighbor) as props
            """
            params = {"id": node_id, "edge_type": edge_type.value}
        else:
            query = """
            MATCH (n:CodeNode {id: $id})-[:RELATIONSHIP]->(neighbor:CodeNode)
            RETURN neighbor.id, neighbor.name, neighbor.node_type, neighbor.file_path, 
                   neighbor.line_number, properties(neighbor) as props
            """
            params = {"id": node_id}
        
        neighbors = []
        with self._driver.session(database=self._database) as session:
            result = session.run(query, **params)
            for record in result:
                props = dict(record["props"])
                for key in ["id", "name", "node_type", "file_path", "line_number"]:
                    props.pop(key, None)
                
                neighbors.append(GraphNode(
                    id=record["neighbor.id"],
                    name=record["neighbor.name"],
                    node_type=NodeType(record["neighbor.node_type"]),
                    file_path=record["neighbor.file_path"],
                    line_number=record["neighbor.line_number"],
                    metadata=props,
                ))
        
        return neighbors
    
    def find_path(self, source_id: str, target_id: str) -> list[GraphNode]:
        """Find the shortest path between two nodes."""
        query = """
        MATCH path = shortestPath(
            (source:CodeNode {id: $source_id})-[:RELATIONSHIP*]->(target:CodeNode {id: $target_id})
        )
        RETURN nodes(path) as nodes
        """
        
        with self._driver.session(database=self._database) as session:
            result = session.run(query, source_id=source_id, target_id=target_id)
            record = result.single()
            
            if record:
                path_nodes = []
                for node in record["nodes"]:
                    path_nodes.append(GraphNode(
                        id=node["id"],
                        name=node["name"],
                        node_type=NodeType(node["node_type"]),
                        file_path=node.get("file_path"),
                        line_number=node.get("line_number"),
                    ))
                return path_nodes
        
        return []
    
    def get_all_nodes(self, node_type: NodeType | None = None) -> list[GraphNode]:
        """Get all nodes, optionally filtered by type."""
        if node_type:
            query = """
            MATCH (n:CodeNode {node_type: $node_type})
            RETURN n.id, n.name, n.node_type, n.file_path, n.line_number, properties(n) as props
            """
            params = {"node_type": node_type.value}
        else:
            query = """
            MATCH (n:CodeNode)
            RETURN n.id, n.name, n.node_type, n.file_path, n.line_number, properties(n) as props
            """
            params = {}
        
        nodes = []
        with self._driver.session(database=self._database) as session:
            result = session.run(query, **params)
            for record in result:
                props = dict(record["props"])
                for key in ["id", "name", "node_type", "file_path", "line_number"]:
                    props.pop(key, None)
                
                nodes.append(GraphNode(
                    id=record["n.id"],
                    name=record["n.name"],
                    node_type=NodeType(record["n.node_type"]),
                    file_path=record["n.file_path"],
                    line_number=record["n.line_number"],
                    metadata=props,
                ))
        
        return nodes
    
    def get_all_edges(self, edge_type: EdgeType | None = None) -> list[GraphEdge]:
        """Get all edges, optionally filtered by type."""
        if edge_type:
            query = """
            MATCH (source:CodeNode)-[r:RELATIONSHIP {edge_type: $edge_type}]->(target:CodeNode)
            RETURN source.id, target.id, r.edge_type, properties(r) as props
            """
            params = {"edge_type": edge_type.value}
        else:
            query = """
            MATCH (source:CodeNode)-[r:RELATIONSHIP]->(target:CodeNode)
            RETURN source.id, target.id, r.edge_type, properties(r) as props
            """
            params = {}
        
        edges = []
        with self._driver.session(database=self._database) as session:
            result = session.run(query, **params)
            for record in result:
                props = dict(record["props"])
                props.pop("edge_type", None)
                
                edges.append(GraphEdge(
                    source=record["source.id"],
                    target=record["target.id"],
                    edge_type=EdgeType(record["r.edge_type"]),
                    metadata=props,
                ))
        
        return edges
    
    def clear(self) -> None:
        """Clear all nodes and edges from the graph."""
        query = "MATCH (n:CodeNode) DETACH DELETE n"
        
        with self._driver.session(database=self._database) as session:
            session.run(query)
    
    def to_dict(self) -> dict[str, Any]:
        """Export the graph to a dictionary."""
        nodes = self.get_all_nodes()
        edges = self.get_all_edges()
        
        return {
            "nodes": [node.to_dict() for node in nodes],
            "edges": [edge.to_dict() for edge in edges],
            "statistics": {
                "node_count": len(nodes),
                "edge_count": len(edges),
            },
        }