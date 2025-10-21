"""Command-line interface for estrattoconto."""

import argparse
import sys
from pathlib import Path

from . import extract_table, enrich_data, __version__


def main() -> int:
    """
    Main CLI entry point for estrattoconto.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        prog="estrattoconto",
        description="Extract and enrich transaction data from Italian bank statement PDFs",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Extract command
    extract_parser = subparsers.add_parser(
        "extract",
        help="Extract transactions from a bank statement PDF",
    )
    extract_parser.add_argument(
        "pdf_path",
        type=str,
        help="Path to the bank statement PDF file",
    )
    extract_parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output CSV file path (default: print to stdout)",
    )
    extract_parser.add_argument(
        "--no-enrich",
        action="store_true",
        help="Skip enrichment, output raw extracted tables",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "extract":
        pdf_path = Path(args.pdf_path)

        if not pdf_path.exists():
            print(f"Error: File not found: {pdf_path}", file=sys.stderr)
            return 1

        if not pdf_path.suffix.lower() == ".pdf":
            print(f"Error: File must be a PDF: {pdf_path}", file=sys.stderr)
            return 1

        try:
            print(f"Extracting tables from {pdf_path}...", file=sys.stderr)
            extracted_tables = extract_table(str(pdf_path))

            # Check if extraction was successful
            if all(df.empty for df in extracted_tables):
                print("Error: No data extracted. Document may be unsupported.", file=sys.stderr)
                return 1

            if args.no_enrich:
                # Output raw transaction table
                result_df = extracted_tables[3]
            else:
                print("Enriching transaction data...", file=sys.stderr)
                result_df = enrich_data(extracted_tables)

            if args.output:
                output_path = Path(args.output)
                result_df.to_csv(output_path, index=False)
                print(f"Success! Output written to: {output_path}", file=sys.stderr)
            else:
                print(result_df.to_csv(index=False))

            return 0

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
