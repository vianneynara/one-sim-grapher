import os
import sys
import re
import glob
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import argparse
import json


class Config:
    """Configuration settings for the ONE Sim Report Grapher tool."""

    # Base directories
    BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
    INPUT_DIR = BASE_DIR / "input"
    OUTPUT_DIR = BASE_DIR / "output"

    # Ensure output dir exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Graph settings
    FIGURE_DPI = 300
    FIGURE_SIZE = (10, 6)
    LINE_STYLES = ['-', '--', '-.', ':']
    MARKERS = ['o', 's', '^', 'D', '*', 'x', '+', 'v', '<', '>']
    COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
              '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

    # Metrics of interest with human display names
    METRICS = {
        'created': 'Message Created',
        'started': 'Message Started',
        'relayed': 'Message Relayed',
        'aborted': 'Message Aborted',
        'dropped': 'Message Dropped',
        'removed': 'Message Removed',
        'delivered': 'Message Delivered',
        'delivery_prob': 'Delivery Probability',
        'overhead_ratio': 'Overhead Ratio',
        'latency_avg': 'Average Latency (s)',
        'latency_med': 'Median Latency (s)',
        'hopcount_avg': 'Average Hop Count',
        'hopcount_med': 'Median Hop Count',
        'buffertime_avg': 'Average Buffer Time (s)',
        'buffertime_med': 'Median Buffer Time (s)',
    }

    # Parameter display names
    PARAMETER_NAMES = {
        'bufferSize': 'Buffer Size',
        'dropPolicy': 'Drop Policy',
        'forwardingStrategy': 'Forwarding Strategy',
        'routingAlgorithm': 'Routing Algorithm'
    }

    # Parameter numeric value extraction rules
    NUMERIC_EXTRACTION = {
        'bufferSize': lambda x: int(re.match(r'(\d+)', x).group(1)) if re.match(r'(\d+)', x) else x,
        'dropPolicy': lambda x: int(x) if x.isdigit() else x
    }


def parse_filename(filename):
    """
    Parse a ONE Simulator report filename to extract configuration parameters.

    Example filename format:
    ProphetMulti-bufferSize@1M-dropPolicy@1-forwardingStrategy@COIN_MessageStatsReport.txt

    Returns a dictionary of parameters.
    """
    basename = os.path.basename(filename)

    # Extract components
    parts = basename.split('-')

    # The first part is always the routing algorithm
    routing_algorithm = parts[0]

    # Parse the remaining parameters
    params = {'routingAlgorithm': routing_algorithm}

    for part in parts[1:]:
        if '_MessageStatsReport.txt' in part:
            # Handle the last part which includes the report suffix
            key_value = part.split('_MessageStatsReport.txt')[0]
            if '@' in key_value:
                key, value = key_value.split('@')
                params[key] = value
        else:
            # Handle regular parameter parts
            if '@' in part:
                key, value = part.split('@')
                params[key] = value

    # Apply numeric extraction rules
    for key, value in list(params.items()):
        if key in Config.NUMERIC_EXTRACTION:
            try:
                params[f"{key}_numeric"] = Config.NUMERIC_EXTRACTION[key](value)
            except (ValueError, AttributeError, TypeError):
                pass  # If conversion fails, use original

    return params


def read_report_file(filename):
    """
    Read a ONE Simulator report file and extract the metric values.

    Returns a dictionary of metric values.
    """
    metrics = {}

    with open(filename, 'r') as f:
        lines = f.readlines()

        # Skip the first line (header)
        for line in lines[1:]:
            line = line.strip()
            if ': ' in line:
                key, value = line.split(': ')
                try:
                    # Try to convert to float
                    value = float(value)
                    if value == float('nan'):
                        value = np.nan
                except ValueError:
                    # Keep as string if not convertible
                    pass
                metrics[key] = value

    return metrics


def collect_data(input_dir):
    """
    Collect data from all report files in the input directory.

    Returns a pandas DataFrame with all metrics and parameters.
    """
    data = []

    # Find all report files
    pattern = os.path.join(input_dir, "*_MessageStatsReport.txt")
    files = glob.glob(pattern)

    for file in files:
        # Parse filename to get parameters
        params = parse_filename(file)

        # Read report file to get metrics
        metrics = read_report_file(file)

        # Combine parameters and metrics
        row = {**params, **metrics}
        data.append(row)

    # Convert to DataFrame
    df = pd.DataFrame(data)

    return df


def plot_comparison(df, metrics, x_axis, compare_by, output_dir, config):
    """
    Create line graphs comparing the specified parameter across different values
    for each metric.

    Args:
        df: DataFrame with the data
        metrics: List of metrics to plot
        x_axis: Parameter to use as x-axis
        compare_by: Parameter to compare (line series)
        output_dir: Directory to save the output
        config: Configuration object
    """
    # Ensure the x_axis has a numeric version
    if f"{x_axis}_numeric" in df.columns:
        x_axis_numeric = f"{x_axis}_numeric"
    else:
        x_axis_numeric = x_axis

    # Get unique values for the comparison parameter
    compare_values = df[compare_by].unique()
    compare_values = sorted(compare_values)

    # Create graphs for each metric
    for metric in metrics:
        if metric not in df.columns:
            print(f"Warning: Metric '{metric}' not found in data. Skipping.")
            continue

        plt.figure(figsize=config.FIGURE_SIZE)

        # Get all other consistent parameters for the title
        constant_params = {}
        for col in df.columns:
            if col not in [x_axis, compare_by, metric, x_axis_numeric] and col not in [f"{p}_numeric" for p in df.columns]:
                if len(df[col].unique()) == 1:
                    constant_params[col] = df[col].iloc[0]

        # Plot each comparison line
        for i, value in enumerate(compare_values):
            # Filter data for this comparison value
            filtered_df = df[df[compare_by] == value].copy()

            # Skip if no data
            if filtered_df.empty:
                continue

            # Sort by x-axis value
            filtered_df = filtered_df.sort_values(x_axis_numeric)

            # Plot line
            style_idx = i % len(config.LINE_STYLES)
            color_idx = i % len(config.COLORS)
            marker_idx = i % len(config.MARKERS)

            plt.plot(
                filtered_df[x_axis_numeric],
                filtered_df[metric],
                linestyle=config.LINE_STYLES[style_idx],
                marker=config.MARKERS[marker_idx],
                color=config.COLORS[color_idx],
                label=f'{config.PARAMETER_NAMES.get(compare_by, compare_by)} {value}'
            )

        # Set labels and title
        x_label = config.PARAMETER_NAMES.get(x_axis, x_axis)
        plt.xlabel(f'{x_label}')

        metric_label = config.METRICS.get(metric, metric)
        plt.ylabel(metric_label)

        # # Create a title with constant parameters
        # const_params_str = ", ".join([f"{config.PARAMETER_NAMES.get(k, k)}: {v}" for k, v in constant_params.items()])
        # if const_params_str:
        #     const_params_str = f"\n({const_params_str})"

        # plt.title(f'{metric_label} vs {x_label} by {config.PARAMETER_NAMES.get(compare_by, compare_by)}{const_params_str}')

        plt.title(
            f'{metric_label} vs {x_label} by {config.PARAMETER_NAMES.get(compare_by, compare_by)} using {constant_params.get("routingAlgorithm")}')

        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()

        # Save the figure
        safe_compare_by = compare_by.replace("/", "_")
        safe_x_axis = x_axis.replace("/", "_")
        safe_metric = metric.replace("/", "_")

        output_file = os.path.join(
            output_dir,
            f"compare_{safe_compare_by}_by_{safe_x_axis}_{safe_metric}.png"
        )
        plt.savefig(output_file, dpi=config.FIGURE_DPI, bbox_inches='tight')
        plt.close()

        print(f"Saved {output_file}")


def save_data_summary(df, output_dir):
    """
    Save a summary of the data for reference.

    Args:
        df: DataFrame with the data
        output_dir: Directory to save the output
    """
    # Save a CSV with all data
    csv_file = os.path.join(output_dir, "all_data.csv")
    df.to_csv(csv_file, index=False)
    print(f"Saved complete dataset to {csv_file}")

    # Save a JSON with parameter and metric information
    info = {
        "parameters": {},
        "metrics": {}
    }

    # Get parameter information
    for col in df.columns:
        if col in Config.METRICS or col.endswith("_numeric"):
            continue

        values = df[col].unique().tolist()
        try:
            values = sorted(values)
        except TypeError:
            pass  # Can't sort mixed types

        info["parameters"][col] = {
            "unique_values": values,
            "count": len(values)
        }

    # Get metric information
    for metric in Config.METRICS.keys():
        if metric in df.columns:
            info["metrics"][metric] = {
                "min": float(df[metric].min()) if not df[metric].isna().all() else None,
                "max": float(df[metric].max()) if not df[metric].isna().all() else None,
                "mean": float(df[metric].mean()) if not df[metric].isna().all() else None,
                "has_nan": bool(df[metric].isna().any())
            }

    # Save the summary
    info_file = os.path.join(output_dir, "data_summary.json")
    with open(info_file, 'w') as f:
        json.dump(info, f, indent=2)

    print(f"Saved data summary to {info_file}")


def main():
    """Main function to generate graphs from ONE Simulator reports."""
    parser = argparse.ArgumentParser(description='Generate graphs from ONE Simulator reports')
    parser.add_argument('--input', '-i', type=str, default=None,
                        help='Input directory containing report files')
    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Output directory for generated graphs')
    parser.add_argument('--x-axis', '-x', type=str, default='bufferSize',
                        help='Parameter to use as x-axis')
    parser.add_argument('--compare-by', '-c', type=str, default='dropPolicy',
                        help='Parameter to compare (create separate lines for each value)')
    parser.add_argument('--metrics', '-m', type=str, nargs='+',
                        help='Selected metrics to plot (default: all)')

    args = parser.parse_args()

    # Initialize configuration
    config = Config()

    # Set input and output directories
    input_dir = args.input if args.input else config.INPUT_DIR
    output_dir = args.output if args.output else config.OUTPUT_DIR

    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    print(f"X-axis parameter: {args.x_axis}")
    print(f"Comparison parameter: {args.compare_by}")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Collect data from report files
    print("Collecting data from report files...")
    df = collect_data(input_dir)

    # Save data summary
    save_data_summary(df, output_dir)

    # Filter metrics if specified
    metrics_to_plot = args.metrics if args.metrics else config.METRICS.keys()

    # Create comparison graphs
    print(f"Creating comparison graphs with {args.x_axis} on x-axis and {args.compare_by} for comparison...")
    plot_comparison(df, metrics_to_plot, args.x_axis, args.compare_by, output_dir, config)

    print("Done!")


if __name__ == "__main__":
    sys.exit(main())