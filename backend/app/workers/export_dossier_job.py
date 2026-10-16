"""Standalone CLI & Batch Job Entrypoint for Forensic SIU Dossier Export.

Can be run locally or invoked as a Nebius Serverless Job / Kubernetes Job:
    python -m app.workers.export_dossier_job <owner_id> <claim_id> [--format json|markdown|html] [--output <path>] [--stdout] [--quiet]
"""

import argparse
import asyncio
import os
import sys

from app.core.errors import NotFoundError
from app.core.logging import logger
from app.schemas.dossier import DossierExportFormat
from app.services.dossier_service import dossier_service

EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_NOT_FOUND = 2
EXIT_UNPROCESSABLE = 3


async def execute_dossier_export_job(
    owner_id: str,
    claim_id: str,
    format_str: str = "json",
    output_path: str | None = None,
    print_stdout: bool = False,
    quiet: bool = False,
) -> int:
    """Executes dossier export pipeline for given claim and owner, returning standard exit codes."""
    try:
        fmt = DossierExportFormat(format_str.lower())
    except ValueError:
        logger.error("Dossier export worker: Unsupported format '%s'. Must be json, markdown, or html.", format_str)
        return EXIT_UNPROCESSABLE

    if not quiet:
        logger.info(
            "Starting dossier export worker job: owner_id=%s claim_id=%s format=%s",
            owner_id,
            claim_id,
            fmt.value,
        )

    try:
        export_resp = await dossier_service.export_dossier(
            owner_id=owner_id,
            claim_id=claim_id,
            format=fmt,
        )

        if output_path:
            dir_name = os.path.dirname(output_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(export_resp.content)
            if not quiet:
                logger.info("Dossier exported to file: %s", output_path)

        if print_stdout or not output_path:
            content = export_resp.content
            if not content.endswith("\n"):
                content += "\n"
            sys.stdout.write(content)

        if not quiet:
            logger.info(
                "Dossier export worker completed successfully: owner_id=%s claim_id=%s format=%s",
                owner_id,
                claim_id,
                fmt.value,
            )
        return EXIT_SUCCESS

    except NotFoundError as err:
        logger.warning(
            "Dossier export worker: Claim not found or unauthorized (404 masking): %s",
            err,
        )
        return EXIT_NOT_FOUND

    except ValueError as err:
        logger.error(
            "Dossier export worker: Unprocessable arguments: %s",
            err,
        )
        return EXIT_UNPROCESSABLE

    except Exception as exc:
        logger.exception("Dossier export worker: Unexpected internal error: %s", exc)
        return EXIT_GENERAL_ERROR


def build_arg_parser() -> argparse.ArgumentParser:
    """Configures command-line arguments for export_dossier_job."""
    parser = argparse.ArgumentParser(
        prog="python -m app.workers.export_dossier_job",
        description="ClaimGuard background worker for generating and exporting forensic SIU dossiers.",
    )
    parser.add_argument("owner_id", help="UUID of the claim owner/tenant")
    parser.add_argument("claim_id", help="UUID of the claim to export")
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "html"],
        default="json",
        dest="format_str",
        help="Export format (json, markdown, html). Default: json",
    )
    parser.add_argument(
        "--output",
        dest="output_path",
        default=None,
        help="Optional local filesystem destination path for the exported dossier",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        dest="print_stdout",
        default=False,
        help="Print the exported dossier content to standard output",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress non-error log messages",
    )
    return parser


def main() -> None:
    """CLI script execution entrypoint."""
    parser = build_arg_parser()
    args = parser.parse_args()

    exit_code = asyncio.run(
        execute_dossier_export_job(
            owner_id=args.owner_id,
            claim_id=args.claim_id,
            format_str=args.format_str,
            output_path=args.output_path,
            print_stdout=args.print_stdout,
            quiet=args.quiet,
        )
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
