"""Standalone CLI & Batch Job Entrypoint for Document Extraction.

Can be run locally or invoked as a Nebius Serverless Job / Kubernetes Job:
    python -m app.workers.extract_job <owner_id> <claim_id> <document_id> [--json] [--quiet]
"""

import argparse
import asyncio
import sys

from app.core.logging import logger
from app.services.extraction_service import (
    DocumentExtractionServiceError,
    EmptyTextLayerError,
    ExtractionNotFoundError,
    UnsupportedDocumentTypeError,
    extraction_service,
)

EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_NOT_FOUND = 2
EXIT_UNPROCESSABLE = 3


async def execute_extraction_job(
    owner_id: str,
    claim_id: str,
    document_id: str,
    emit_json: bool = False,
    quiet: bool = False,
) -> int:
    """Executes extraction pipeline for given document and returns corresponding exit code."""
    if not quiet:
        logger.info(
            "Starting extraction worker job: document_id=%s claim_id=%s owner_id=%s",
            document_id,
            claim_id,
            owner_id,
        )

    try:
        extraction = await extraction_service.extract_document(
            owner_id=owner_id,
            claim_id=claim_id,
            document_id=document_id,
        )

        if emit_json:
            sys.stdout.write(extraction.model_dump_json(indent=2) + "\n")

        if not quiet:
            logger.info(
                "Extraction worker completed successfully: document_id=%s all_grounded=%s",
                document_id,
                extraction.all_entities_grounded,
            )
        return EXIT_SUCCESS

    except ExtractionNotFoundError as err:
        logger.warning(
            "Extraction worker: Document not found or unauthorized for owner (404 masking): %s",
            err,
        )
        return EXIT_NOT_FOUND

    except (UnsupportedDocumentTypeError, EmptyTextLayerError) as err:
        logger.error(
            "Extraction worker: Unprocessable document format or empty text layer: code=%s message=%s",
            getattr(err, "code", "UNPROCESSABLE"),
            err,
        )
        return EXIT_UNPROCESSABLE

    except DocumentExtractionServiceError as err:
        logger.error(
            "Extraction worker: Pipeline operation failed: code=%s message=%s",
            err.code,
            err,
        )
        return EXIT_GENERAL_ERROR

    except Exception as exc:
        logger.exception("Extraction worker: Unexpected internal error: %s", exc)
        return EXIT_GENERAL_ERROR


def build_arg_parser() -> argparse.ArgumentParser:
    """Configures command-line arguments for extract_job."""
    parser = argparse.ArgumentParser(
        prog="python -m app.workers.extract_job",
        description="ClaimGuard background worker for document text extraction and entity grounding.",
    )
    parser.add_argument("owner_id", help="UUID of the claim/document owner")
    parser.add_argument("claim_id", help="UUID of the parent claim")
    parser.add_argument("document_id", help="UUID of the document to extract")
    parser.add_argument(
        "--json",
        action="store_true",
        dest="emit_json",
        default=False,
        help="Print the grounded extraction JSON payload to stdout on success",
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
        execute_extraction_job(
            owner_id=args.owner_id,
            claim_id=args.claim_id,
            document_id=args.document_id,
            emit_json=args.emit_json,
            quiet=args.quiet,
        )
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
