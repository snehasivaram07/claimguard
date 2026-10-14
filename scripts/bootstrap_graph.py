import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.graph.bootstrap import bootstrap_graph_schema
from app.graph.client import graph_manager


def main():
    print("Connecting to FalkorDB...")
    if not graph_manager.check_health(max_retries=5, retry_delay=1.0):
        print("Error: Could not connect to FalkorDB service.")
        sys.exit(1)

    graph = graph_manager.get_graph()
    bootstrap_graph_schema(graph)
    print("Graph schema initialized successfully.")


if __name__ == "__main__":
    main()
