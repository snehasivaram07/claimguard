"""Standalone CLI & Batch Job Entrypoint for Claim Intelligence & Cross-Validation.

Can be run locally or invoked as a Nebius Serverless Job / Kubernetes Job:
    python -m app.workers.analyze_claim_job <owner_id> <claim_id> [--json] [--quiet]
"""

import argparse
import asyncio
import sys

from app.core.errors import BadRequestError, NotFoundError
from app.core.logging import logger
from app.services.claim_intelligence_service import (
    ClaimNotFoundError,
    claim_intelligence_service,
)

EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_NOT_FOUND = 2
EXIT_UNPROCESSABLE = 3


async def execute_claim_analysis_job(
    owner_id: str,
    claim_id: str,
    emit_json: bool = False,
    quiet: bool = False,
) -> int:
    """Executes claim intelligence pipeline for given claim and returns corresponding exit code."""
    if not quiet:
        logger.info(
            "Starting claim intelligence worker job: claim_id=%s owner_id=%s",
            claim_id,
            owner_id,
        )

    try:
        analysis = await claim_intelligence_service.analyze_claim(
            owner_id=owner_id,
            claim_id=claim_id,
        )

        if emit_json:
            sys.stdout.write(analysis.model_dump_json(indent=2) + "\n")

        if not quiet:
            logger.info(
                "Claim intelligence worker completed successfully: claim_id=%s risk_score=%s discrepancies=%d",
                claim_id,
                analysis.overall_risk_score,
                len(analysis.discrepancies),
            )
        return EXIT_SUCCESS

    except (ClaimNotFoundError, NotFoundError) as err:
        logger.warning(
            "Claim intelligence worker: Claim not found or unauthorized for owner (404 masking): %s",
            err,
        )
        return EXIT_NOT_FOUND

    except (BadRequestError, ValueError) as err:
        logger.error(
            "Claim intelligence worker: Unprocessable claim or insufficient documents: %s",
            err,
        )
        return EXIT_UNPROCESSABLE

    except Exception as exc:
        logger.exception("Claim intelligence worker: Unexpected internal error: %s", exc)
        return EXIT_GENERAL_ERROR


def build_arg_parser() -> argparse.ArgumentParser:
    """Configures command-line arguments for analyze_claim_job."""
    parser = argparse.ArgumentParser(
        prog="python -m app.workers.analyze_claim_job",
        description="ClaimGuard background worker for multi-document cross-validation, timeline reconstruction, and contradiction detection.",
    )
    parser.add_argument("owner_id", help="UUID of the claim owner")
    parser.add_argument("claim_id", help="UUID of the claim to analyze")
    parser.add_argument(
        "--json",
        action="store_true",
        dest="emit_json",
        default=False,
        help="Print the structured intelligence analysis JSON payload to stdout on success",
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
        execute_claim_analysis_job(
            owner_id=args.owner_id,
            claim_id=args.claim_id,
            emit_json=args.emit_json,
            quiet=args.quiet,
        )
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
