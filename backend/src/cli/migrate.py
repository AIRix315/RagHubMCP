"""CLI command for vector store migration.

Usage:
    python -m src.cli.migrate [options]

Examples:
    # Migrate all collections from ChromaDB to local Qdrant
    python -m src.cli.migrate

    # Migrate specific collections
    python -m src.cli.migrate --collections docs code

    # Migrate to Qdrant remote server
    python -m src.cli.migrate --qdrant-mode remote --qdrant-host localhost --qdrant-port 6333
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def print_progress(current: int, total: int, message: str) -> None:
    """Print migration progress to console.

    Args:
        current: Current progress count
        total: Total count
        message: Status message
    """
    if total > 0:
        percent = (current / total) * 100
        print(f"\r[{percent:6.2f}%] {message}", end="", flush=True)
    else:
        print(f"\r{message}", end="", flush=True)


def print_result(result: dict[str, Any]) -> None:
    """Print migration result summary.

    Args:
        result: Migration result dictionary
    """
    print("\n" + "=" * 60)
    print("MIGRATION RESULT")
    print("=" * 60)

    status = "✓ SUCCESS" if result.get("success") else "✗ FAILED"
    print(f"Status: {status}")
    print(f"Collections migrated: {result.get('collections_migrated', 0)}")
    print(f"Documents migrated: {result.get('documents_migrated', 0)}")
    print(f"Duration: {result.get('duration_seconds', 0):.2f}s")

    if result.get("collections"):
        print("\nCollections:")
        for coll in result["collections"]:
            status_icon = "✓" if coll.get("success") else "✗"
            print(f"  {status_icon} {coll['name']}: {coll.get('documents_migrated', 0)} documents")

    if result.get("warnings"):
        print("\nWarnings:")
        for warning in result["warnings"]:
            print(f"  ⚠ {warning}")

    if result.get("errors"):
        print("\nErrors:")
        for error in result["errors"]:
            print(f"  ✗ {error}")

    print("=" * 60)


def main() -> int:
    """Main entry point for CLI migration tool."""
    parser = argparse.ArgumentParser(
        description="Migrate data between vector store providers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Migrate all collections from ChromaDB to local Qdrant
  python -m src.cli.migrate

  # Migrate specific collections
  python -m src.cli.migrate --collections docs code

  # Migrate to Qdrant remote server
  python -m src.cli.migrate --qdrant-mode remote --qdrant-host localhost

  # Migrate to Qdrant Cloud
  python -m src.cli.migrate --qdrant-mode cloud --qdrant-url https://xxx.cloud.qdrant.io --qdrant-api-key YOUR_KEY
        """,
    )

    # Source options
    parser.add_argument(
        "--chroma-dir",
        default="./data/chroma",
        help="ChromaDB persistence directory (default: ./data/chroma)",
    )

    # Target options
    parser.add_argument(
        "--qdrant-mode",
        choices=["memory", "local", "remote", "cloud"],
        default="local",
        help="Qdrant mode (default: local)",
    )
    parser.add_argument(
        "--qdrant-path",
        default="./data/qdrant",
        help="Qdrant storage path for local mode (default: ./data/qdrant)",
    )
    parser.add_argument(
        "--qdrant-host",
        help="Qdrant server host for remote mode",
    )
    parser.add_argument(
        "--qdrant-port",
        type=int,
        help="Qdrant server port for remote mode",
    )
    parser.add_argument(
        "--qdrant-url",
        help="Qdrant Cloud URL",
    )
    parser.add_argument(
        "--qdrant-api-key",
        help="Qdrant Cloud API key",
    )

    # Migration options
    parser.add_argument(
        "--collections",
        nargs="+",
        help="Specific collections to migrate (default: all)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for migration (default: 100)",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip data integrity verification",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List collections without migrating",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Dry run: list collections and exit
    if args.dry_run:
        try:
            from providers.vectorstore import ChromaProvider

            print("Scanning ChromaDB collections...")
            source = ChromaProvider(persist_dir=args.chroma_dir)

            collections = source.list_collections()
            if not collections:
                print("No collections found.")
                return 0

            total_docs = 0
            print(f"\nFound {len(collections)} collection(s):")
            print("-" * 40)

            for name in collections:
                count = source.count(name)
                total_docs += count
                print(f"  {name}: {count} documents")

            print("-" * 40)
            print(f"Total: {total_docs} documents")

            return 0

        except Exception as e:
            logger.error(f"Failed to scan collections: {e}")
            return 1

    # Perform migration
    print("=" * 60)
    print("VECTOR STORE MIGRATION")
    print("=" * 60)
    print(f"Source: ChromaDB ({args.chroma_dir})")
    print(f"Target: Qdrant ({args.qdrant_mode})")
    if args.collections:
        print(f"Collections: {', '.join(args.collections)}")
    else:
        print("Collections: all")
    print(f"Batch size: {args.batch_size}")
    print(f"Verify: {not args.no_verify}")
    print("=" * 60)
    print()

    try:
        from utils.migrate import migrate_chroma_to_qdrant

        # Build Qdrant config
        qdrant_kwargs: dict[str, Any] = {
            "qdrant_mode": args.qdrant_mode,
            "qdrant_path": args.qdrant_path,
        }
        if args.qdrant_host:
            qdrant_kwargs["qdrant_host"] = args.qdrant_host
        if args.qdrant_port:
            qdrant_kwargs["qdrant_port"] = args.qdrant_port
        if args.qdrant_url:
            qdrant_kwargs["qdrant_url"] = args.qdrant_url
        if args.qdrant_api_key:
            qdrant_kwargs["qdrant_api_key"] = args.qdrant_api_key

        result = migrate_chroma_to_qdrant(
            chroma_persist_dir=args.chroma_dir,
            collections=args.collections,
            batch_size=args.batch_size,
            progress_callback=print_progress,
            verify=not args.no_verify,
            **qdrant_kwargs,
        )

        print_result(result.to_dict())

        return 0 if result.success else 1

    except KeyboardInterrupt:
        print("\nMigration cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        print(f"\n✗ Migration failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
