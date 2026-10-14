import time

from falkordb import FalkorDB, Graph

from app.core.config import settings
from app.core.logging import logger


class FalkorDBConnectionManager:
    """Manages the FalkorDB connection and graph instance with health checking and retries."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        password: str | None = None,
        graph_name: str | None = None,
    ):
        self.host = host or settings.FALKORDB_HOST
        self.port = port or settings.FALKORDB_PORT
        self.password = password or (settings.FALKORDB_PASSWORD if settings.FALKORDB_PASSWORD else None)
        self.graph_name = graph_name or settings.FALKORDB_GRAPH_NAME
        self._db: FalkorDB | None = None
        self._graph: Graph | None = None

    def get_client(self) -> FalkorDB:
        if self._db is None:
            self._db = FalkorDB(
                host=self.host,
                port=self.port,
                password=self.password,
            )
        return self._db

    def get_graph(self) -> Graph:
        if self._graph is None:
            db = self.get_client()
            self._graph = db.select_graph(self.graph_name)
        return self._graph

    def check_health(self, max_retries: int = 3, retry_delay: float = 0.5) -> bool:
        """Verifies connectivity to FalkorDB by executing a ping query with backoff."""
        for attempt in range(1, max_retries + 1):
            try:
                graph = self.get_graph()
                result = graph.query("RETURN 1 AS ping")
                if result and result.result_set:
                    return True
            except Exception as e:
                logger.warning(
                    f"FalkorDB health check attempt {attempt}/{max_retries} failed: {e}"
                )
                if attempt < max_retries:
                    time.sleep(retry_delay * attempt)
        return False

    def close(self):
        """Cleanly releases any connection resources."""
        self._graph = None
        self._db = None


graph_manager = FalkorDBConnectionManager()


def get_graph_client() -> Graph:
    """Dependency / provider for the active FalkorDB graph instance."""
    return graph_manager.get_graph()
