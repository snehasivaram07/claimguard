from typing import Any

from falkordb import Graph, Node

from app.graph.client import get_graph_client


class BaseGraphRepository:
    """Base class for tenant-scoped FalkorDB repositories.

    CRITICAL INVARIANT:
    All Cypher queries in ClaimGuard are strictly confined to methods of repositories
    inheriting from BaseGraphRepository. Every query must be parameterized, and every
    method must accept and enforce an authenticated owner_id.
    """

    SCHEMA_VERSION: int = 1

    def __init__(self, graph: Graph | None = None):
        self._graph = graph

    @property
    def graph(self) -> Graph:
        if self._graph is None:
            self._graph = get_graph_client()
        return self._graph

    def _execute(self, query: str, params: dict[str, Any] | None = None) -> list[list[Any]]:
        """Executes a strictly parameterized Cypher query and returns result rows."""
        safe_params = params or {}
        result = self.graph.query(query, safe_params)
        return result.result_set if result and result.result_set else []

    @staticmethod
    def _node_to_dict(node_or_record: Any) -> dict[str, Any] | None:
        """Safely extracts properties dictionary from a FalkorDB Node or raw dict."""
        if node_or_record is None:
            return None
        if isinstance(node_or_record, Node):
            return dict(node_or_record.properties)
        if isinstance(node_or_record, dict):
            return dict(node_or_record)
        return None
