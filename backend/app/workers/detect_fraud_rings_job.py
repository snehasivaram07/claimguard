"""Standalone CLI & Batch Job Entrypoint for Graph Fraud Ring Detection & Network Analysis.

Can be run locally or invoked as a Nebius Serverless Job / Kubernetes Job:
    python -m app.workers.detect_fraud_rings_job <owner_id> [--min-shared <N>] [--json] [--quiet]
"""

import argparse
import asyncio
import json
import sys

from app.core.config import settings
from app.core.errors import NotFoundError
from app.core.logging import logger
from app.services.fraud_ring_service import fraud_ring_service

EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_NOT_FOUND = 2
EXIT_UNPROCESSABLE = 3


async def execute_fraud_ring_detection_job(
    owner_id: str,
    min_shared: int | None = None,
    emit_json: bool = False,
    quiet: bool = False,
) -> int:
    """Executes fraud ring detection pipeline for given owner and returns corresponding exit code."""
    threshold = min_shared if min_shared is not None else settings.FRAUD_RING_MIN_SHARED_ENTITIES
    if threshold < 1:
        logger.error("Fraud ring worker: min_shared must be at least 1, got %d", threshold)
        return EXIT_UNPROCESSABLE

    if not quiet:
        logger.info(
            "Starting fraud ring detection worker job: owner_id=%s min_shared=%d",
            owner_id,
            threshold,
        )

    try:
        rings = await fraud_ring_service.detect_fraud_rings(
            owner_id=owner_id,
            min_shared=threshold,
        )

        if emit_json:
            payload = [r.model_dump() for r in rings]
            sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")

        if not quiet:
            logger.info(
                "Fraud ring detection worker completed successfully: owner_id=%s rings_found=%d",
                owner_id,
                len(rings),
            )
        return EXIT_SUCCESS

    except NotFoundError as err:
        logger.warning(
            "Fraud ring worker: Owner not found or unauthorized (404 masking): %s",
            err,
        )
        return EXIT_NOT_FOUND

    except ValueError as err:
        logger.error(
            "Fraud ring worker: Unprocessable arguments: %s",
            err,
        )
        return EXIT_UNPROCESSABLE

    except Exception as exc:
        logger.exception("Fraud ring worker: Unexpected internal error: %s", exc)
        return EXIT_GENERAL_ERROR


def build_arg_parser() -> argparse.ArgumentParser:
    """Configures command-line arguments for detect_fraud_rings_job."""
    parser = argparse.ArgumentParser(
        prog="python -m app.workers.detect_fraud_rings_job",
        description="ClaimGuard background worker for multi-claim graph traversal and fraud ring cluster detection.",
    )
    parser.add_argument("owner_id", help="UUID of the claim owner/tenant")
    parser.add_argument(
        "--min-shared",
        type=int,
        default=2,
        help="Minimum number of shared entities required to form a collusion ring (default: 2)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="emit_json",
        default=False,
        help="Print the detected fraud rings JSON payload to stdout on success",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress informational log messages",
    )
    return parser


def main() -> None:
    """CLI script entrypoint."""
    parser = build_arg_parser()
    args = parser.parse_args()

    exit_code = asyncio.run(
        execute_fraud_ring_detection_job(
            owner_id=args.owner_id,
            min_shared=args.min_shared,
            emit_json=args.emit_json,
            quiet=args.quiet,
        )
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
