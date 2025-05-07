#!/usr/bin/env python3
"""
ONE Sim Report Grapher

A tool for generating graphs from ONE Simulator reports.
"""
import sys
import argparse
from pathlib import Path

from src.utils import (
    setup_logger,
    MessageStatsParser,
    create_comparison_graphs,
    create_multi_router_comparison,
    INPUT_DIR,
    OUTPUT_DIR
)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate graphs from ONE Simulator report files"
    )

    parser.add_argument(
        "-i", "--input-dir",
        type=Path,
        default=INPUT_DIR,
        help="Directory containing report files (default: ./input)"
    )

    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Directory to save generated graphs (default: ./output)"
    )

    parser.add_argument(
        "-c", "--comparison",
        action="store_true",
        help="Generate line comparison graphs between different routers"
    )

    parser.add_argument(
        "-m", "--multi-comparison",
        action="store_true",
        help="Generate multi-router comparison graphs (bar charts and trend lines)"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)"
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    # Setup logging
    logger = setup_logger(args.log_level)
    logger.info("Starting ONE Sim Report Grapher")

    # Create output directory if it doesn't exist
    args.output_dir.mkdir(exist_ok=True, parents=True)

    # Process the report files
    logger.info(f"Processing files from {args.input_dir}")
    parser = MessageStatsParser(input_dir=args.input_dir, output_dir=args.output_dir)
    parser.process()

    # Generate comparison graphs if requested
    if args.comparison and parser.data:
        logger.info("Generating line comparison graphs")
        create_comparison_graphs(parser.data, args.output_dir)

    # Generate multi-router comparison graphs if requested
    if args.multi_comparison and parser.data:
        logger.info("Generating multi-router comparison graphs")
        create_multi_router_comparison(parser.data, args.output_dir)

    # Always create the multi-router comparison if more than one router is found
    # (since this is the main request from the user)
    router_count = len(parser.data.keys())
    if router_count > 1 and not args.multi_comparison:
        logger.info(f"Found {router_count} different routers, generating comparisons automatically")
        create_multi_router_comparison(parser.data, args.output_dir)

    logger.info(f"All graphs saved to {args.output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())