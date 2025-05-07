"""
Helper functions for the ONE Sim Report Grapher tool.

This module provides utility functions used across the application.
"""
import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import matplotlib.pyplot as plt
import numpy as np

from .config import METRICS, LINE_STYLES, MARKERS, COLORS


def setup_logger(level: str = "INFO") -> logging.Logger:
    """Set up and configure the logger."""
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")

    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    return logging.getLogger()


def find_report_files(directory: Path, pattern: str = "*_MessageStatsReport.txt") -> List[Path]:
    """Find all report files in directory matching pattern."""
    return list(directory.glob(pattern))


def extract_unique_params(data: Dict[str, Dict[str, Dict[float, Dict]]]) -> Dict[str, List[str]]:
    """Extract unique router names and parameter names from data."""
    unique_params = {}

    for router_name, param_data in data.items():
        unique_params[router_name] = list(param_data.keys())

    return unique_params


def create_comparison_graphs(data: Dict[str, Dict[str, Dict[float, Dict]]],
                            output_dir: Path) -> None:
    """Create comparison graphs for routers with the same parameter types."""
    # Group by parameter type
    param_groups = {}

    for router_name, router_data in data.items():
        for param_name, param_values in router_data.items():
            if param_name not in param_groups:
                param_groups[param_name] = {}
            param_groups[param_name][router_name] = param_values

    # For each parameter type and metric, create a comparison graph
    for param_name, routers in param_groups.items():
        for metric_key, metric_name in METRICS.items():
            plt.figure(figsize=(12, 7))

            # Check if we have any valid data points for this metric
            has_valid_data = False

            for i, (router_name, param_values) in enumerate(routers.items()):
                x_values = sorted(param_values.keys())
                y_values = [param_values[x].get(metric_key, float('nan')) for x in x_values]

                # Filter out NaN values
                valid_points = [(x, y) for x, y in zip(x_values, y_values) if not np.isnan(y)]
                if not valid_points:
                    continue

                has_valid_data = True
                x_values, y_values = zip(*valid_points)

                # Use cycling styles
                style_idx = i % len(LINE_STYLES)
                marker_idx = i % len(MARKERS)
                color_idx = i % len(COLORS)

                plt.plot(x_values, y_values,
                         marker=MARKERS[marker_idx],
                         linestyle=LINE_STYLES[style_idx],
                         color=COLORS[color_idx],
                         linewidth=2,
                         markersize=8,
                         label=router_name)

            # Skip saving if no valid data
            if not has_valid_data:
                plt.close()
                continue

            plt.title(f"Comparison of {metric_name} vs {param_name}")
            plt.xlabel(param_name)
            plt.ylabel(metric_name)
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.legend(loc='best')

            # Save the figure
            output_file = output_dir / f"comparison_{param_name}_{metric_key}.png"
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()


def create_multi_router_comparison(data: Dict[str, Dict[str, Dict[float, Dict]]],
                                  output_dir: Path) -> None:
    """Create summary comparison graphs for all routers with the same parameter.

    This creates line graphs showing each router's performance across different
    parameter values.
    """
    # Get all unique routers and parameters
    all_routers = set()
    param_metrics = {}

    for router_name, router_data in data.items():
        all_routers.add(router_name)
        for param_name, param_values in router_data.items():
            if param_name not in param_metrics:
                param_metrics[param_name] = set()

            # Get all parameter values for this param type
            for param_value in param_values.keys():
                param_metrics[param_name].add(param_value)

    # For each metric, create a bar chart comparing all routers at each parameter value
    for param_name, param_values in param_metrics.items():
        param_values = sorted(param_values)

        for metric_key, metric_name in METRICS.items():
            # Bar chart comparing routers at each parameter value
            for param_value in param_values:
                plt.figure(figsize=(10, 6))

                # Collect values for each router at this parameter value
                router_values = []
                router_names = []

                for router_name in sorted(all_routers):
                    if (router_name in data and
                        param_name in data[router_name] and
                        param_value in data[router_name][param_name] and
                        metric_key in data[router_name][param_name][param_value] and
                        not np.isnan(data[router_name][param_name][param_value][metric_key])):

                        router_names.append(router_name)
                        router_values.append(data[router_name][param_name][param_value][metric_key])

                if not router_values:
                    plt.close()
                    continue

                # Create bar chart
                bars = plt.bar(range(len(router_names)), router_values, color=COLORS[:len(router_names)])
                plt.xticks(range(len(router_names)), router_names, rotation=45, ha='right')
                plt.title(f"{metric_name} for {param_name}={param_value}")
                plt.ylabel(metric_name)
                plt.tight_layout()

                # Add value labels on top of bars
                for bar in bars:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height,
                            f'{height:.4f}',
                            ha='center', va='bottom', rotation=0)

                # Save the figure
                output_file = output_dir / f"bar_comparison_{param_name}_{param_value}_{metric_key}.png"
                plt.savefig(output_file, dpi=300, bbox_inches='tight')
                plt.close()

            # Line graph showing trends for each router across parameter values
            plt.figure(figsize=(12, 7))
            has_valid_data = False

            for i, router_name in enumerate(sorted(all_routers)):
                if router_name not in data or param_name not in data[router_name]:
                    continue

                router_param_values = data[router_name][param_name]
                x_values = []
                y_values = []

                for pv in sorted(param_values):
                    if pv in router_param_values and metric_key in router_param_values[pv]:
                        value = router_param_values[pv].get(metric_key, float('nan'))
                        if not np.isnan(value):
                            x_values.append(pv)
                            y_values.append(value)

                if not x_values:
                    continue

                has_valid_data = True
                style_idx = i % len(LINE_STYLES)
                marker_idx = i % len(MARKERS)
                color_idx = i % len(COLORS)

                plt.plot(x_values, y_values,
                        marker=MARKERS[marker_idx],
                        linestyle=LINE_STYLES[style_idx],
                        color=COLORS[color_idx],
                        linewidth=2,
                        markersize=8,
                        label=router_name)

            if not has_valid_data:
                plt.close()
                continue

            plt.title(f"{metric_name} vs {param_name} for All Routers")
            plt.xlabel(param_name)
            plt.ylabel(metric_name)
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.legend(loc='best')

            # Save the figure
            output_file = output_dir / f"line_comparison_all_routers_{param_name}_{metric_key}.png"
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()


def sanitize_filename(name: str) -> str:
    """Convert a string to a valid filename."""
    # Replace invalid characters with underscores
    return re.sub(r'[\\/*?:"<>|]', "_", name)