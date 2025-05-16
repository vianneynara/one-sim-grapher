#!/usr/bin/env python3
"""
ONE Sim Report Grouper

A tool for grouping reports of ONE Simulator based on file naming conventions.
"""
import sys
import argparse
import shutil
from pathlib import Path
from typing import Dict, List, Optional


class ReportFile:
    """Represents a single report file with its metadata extracted from the filename."""

    def __init__(self, file_path: Path):
        self.path = file_path
        self.name = file_path.name
        self.metadata = self._extract_metadata()

    def _extract_metadata(self) -> Dict[str, str]:
        """Extract metadata from the filename."""
        # Extract the main part of the filename (before _MessageStatsReport.txt)
        main_part = self.name.split("_MessageStatsReport.txt")[0]

        # Split by hyphen to get the different sections
        sections = main_part.split("-")

        # The first section is always the routing algorithm
        metadata = {"routingAlgorithm": sections[0]}

        # Process the remaining sections (key@value pairs)
        for section in sections[1:]:
            if "@" in section:
                key, value = section.split("@", 1)
                metadata[key] = value

        return metadata

    def get_value(self, key: str) -> Optional[str]:
        """Get a metadata value by key."""
        return self.metadata.get(key)


class Grouper:
    """Groups report files based on specified parameters."""

    def __init__(self, input_dir: Path, output_dir: Path, group_by: Optional[str]):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.group_by = group_by
        self.reports: List[ReportFile] = []

        # Load and process reports
        self.load_reports()
        self.group_reports()

    def load_reports(self):
        """Load reports from the input directory."""
        for file_path in self.input_dir.glob("*_MessageStatsReport.txt"):
            if file_path.is_file():
                report = ReportFile(file_path)
                self.reports.append(report)

        print(f"Loaded {len(self.reports)} report files.")

    def group_reports(self):
        """Group reports based on the specified parameter."""
        if not self.reports:
            print("No reports found to group.")
            return

        # If group_by not specified, use the last parameter in the first file as default
        if self.group_by is None:
            # Get all keys from the first report's metadata
            keys = list(self.reports[0].metadata.keys())
            # The routingAlgorithm is always first, so skip it
            keys.remove("routingAlgorithm")
            # Use the last parameter as default group_by
            self.group_by = keys[-1]
            print(f"No group-by parameter specified. Using default: {self.group_by}")

        # Create a dictionary to store groups
        groups = {}

        # Group reports by the specified parameter
        for report in self.reports:
            value = report.get_value(self.group_by)
            if value:
                group_key = f"{self.group_by}@{value}"
                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append(report)

        # Create output directories and copy files
        for group_name, group_reports in groups.items():
            group_dir = self.output_dir / group_name
            group_dir.mkdir(exist_ok=True, parents=True)

            print(f"Group '{group_name}' has {len(group_reports)} files.")

            for report in group_reports:
                dest_file = group_dir / report.name
                shutil.copy2(report.path, dest_file)
                print(f"  - Copied {report.name}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Group similar reports from ONE Simulator report files"
    )

    parser.add_argument(
        "-i", "--input-dir",
        type=Path,
        default=Path("./input"),
        help="Directory containing report files (default: ./input)"
    )

    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path("./output"),
        help="Directory to save grouped reports (default: ./output)"
    )

    parser.add_argument(
        "-g", "--group-by",
        help="Group reports by this parameter (e.g., 'forwardingStrategy', 'bufferSize', 'dropPolicy', etc.)",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # Verify input directory exists
    if not args.input_dir.exists():
        print(f"Error: Input directory '{args.input_dir}' does not exist.")
        return 1

    # Create output directory if it doesn't exist
    args.output_dir.mkdir(exist_ok=True, parents=True)

    grouper = Grouper(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        group_by=args.group_by
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())