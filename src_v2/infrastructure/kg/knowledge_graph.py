"""Knowledge graph infrastructure for standard relations using NetworkX."""

from __future__ import annotations

import networkx as nx

from src_v2.domain.ingestion.entities import DocumentContentType, Standard
from src_v2.domain.shared.value_objects import StandardId

__all__ = ["StandardKnowledgeGraph", "StandardRepositoryImpl"]


class StandardKnowledgeGraph:
    """Directed graph of Standard relations using NetworkX."""

    def __init__(self) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()

    def build_from_standards(self, standards: list[Standard]) -> None:
        """Build graph nodes and edges from Standard entities."""
        for standard in standards:
            self.graph.add_node(standard.id, standard=standard)
            for relation in standard.relations:
                self.graph.add_edge(standard.id, relation, type="relates_to")

    def add_standard(self, standard: Standard) -> None:
        """Add a single standard and its relations to the graph."""
        self.graph.add_node(standard.id, standard=standard)
        for relation in standard.relations:
            self.graph.add_edge(standard.id, relation, type="relates_to")

    def get_related_ids(self, standard_id: StandardId, max_depth: int = 2) -> list[StandardId]:
        """BFS traversal up to max_depth, returns related StandardIds (not including start)."""
        if standard_id not in self.graph:
            return []
        related: list[StandardId] = []
        visited: set[StandardId] = {standard_id}
        queue: list[tuple[StandardId, int]] = [(standard_id, 0)]
        while queue:
            current, depth = queue.pop(0)
            if depth >= max_depth:
                continue
            for successor in self.graph.successors(current):
                if successor not in visited:
                    visited.add(successor)
                    related.append(successor)
                    queue.append((successor, depth + 1))
        return related

    def get_subgraph_context(
        self, standard_id: StandardId, depth: int = 1
    ) -> list[Standard]:
        """Return the target standard plus related standards as list[Standard]."""
        if standard_id not in self.graph:
            return []
        related_ids = [standard_id] + self.get_related_ids(standard_id, depth)
        result: list[Standard] = []
        for sid in related_ids:
            node_data = self.graph.nodes.get(sid)
            if node_data is not None:
                standard = node_data.get("standard")
                if standard is not None:
                    result.append(standard)
        return result

    def has_standard(self, standard_id: StandardId) -> bool:
        return standard_id in self.graph

    def get_standard(self, standard_id: StandardId) -> Standard | None:
        node_data = self.graph.nodes.get(standard_id)
        if node_data is None:
            return None
        return node_data.get("standard")

    def __len__(self) -> int:
        return self.graph.number_of_nodes()

    def __contains__(self, standard_id: StandardId) -> bool:
        return self.has_standard(standard_id)


class StandardRepositoryImpl:
    """IStandardRepository implementation backed by StandardKnowledgeGraph."""

    def __init__(self, knowledge_graph: StandardKnowledgeGraph) -> None:
        self._standards: dict[StandardId, Standard] = {}
        self._kg = knowledge_graph

    def store_standard(self, standard: Standard) -> None:
        self._standards[standard.id] = standard
        self._kg.add_standard(standard)

    def find_by_id(self, id: StandardId) -> Standard | None:
        return self._standards.get(id)

    def find_by_content_type(
        self, content_type: DocumentContentType
    ) -> list[Standard]:
        return [s for s in self._standards.values() if s.content_type == content_type]

    def find_related(self, standard_id: StandardId, depth: int) -> list[StandardId]:
        return self._kg.get_related_ids(standard_id, max_depth=depth)
