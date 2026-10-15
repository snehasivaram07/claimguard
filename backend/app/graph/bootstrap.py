from falkordb import Graph

from app.core.logging import logger

INDEX_QUERIES = [
    # Primary identifiers
    "CREATE INDEX FOR (u:User) ON (u.id)",
    "CREATE INDEX FOR (c:Claim) ON (c.id)",
    "CREATE INDEX FOR (d:Document) ON (d.id)",
    # Tenant scoping indexes for fast multi-tenant lookup
    "CREATE INDEX FOR (c:Claim) ON (c.owner_id)",
    "CREATE INDEX FOR (d:Document) ON (d.owner_id)",
    "CREATE INDEX FOR (d:Document) ON (d.content_hash)",
    # Phase 3 Entity indexes
    "CREATE INDEX FOR (p:Person) ON (p.id)",
    "CREATE INDEX FOR (p:Person) ON (p.owner_id)",
    "CREATE INDEX FOR (p:Person) ON (p.claim_id)",
    "CREATE INDEX FOR (o:Organization) ON (o.id)",
    "CREATE INDEX FOR (o:Organization) ON (o.owner_id)",
    "CREATE INDEX FOR (o:Organization) ON (o.claim_id)",
    "CREATE INDEX FOR (v:Vehicle) ON (v.id)",
    "CREATE INDEX FOR (v:Vehicle) ON (v.owner_id)",
    "CREATE INDEX FOR (v:Vehicle) ON (v.claim_id)",
]


def bootstrap_graph_schema(graph: Graph) -> None:
    """Idempotently bootstrap indexes and constraints in the FalkorDB claimguard graph."""
    logger.info("Bootstrapping FalkorDB schema for graph: %s", graph.name)

    for query in INDEX_QUERIES:
        try:
            graph.query(query)
            logger.info("Successfully executed index query: %s", query)
        except Exception as e:
            # FalkorDB raises an exception if the index already exists. Treat as idempotent success.
            err_msg = str(e).lower()
            if "already exists" in err_msg or "already indexed" in err_msg:
                logger.debug("Index already exists: %s", query)
            else:
                logger.warning("Index query execution note for '%s': %s", query, e)

    logger.info("FalkorDB schema bootstrap completed successfully.")
