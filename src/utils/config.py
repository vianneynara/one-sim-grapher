"""
Configuration settings for the ONE Sim Report Grapher tool.

This module defines paths, settings, and constants used for the application.
"""
import os
from pathlib import Path

# Base directories
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_DIR = BASE_DIR / "../input"
OUTPUT_DIR = BASE_DIR / "../output"

# Ensure output dir exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# File patterns
STATS_FILE_PATTERN = r"(.+)-([\w@\d]+)_MessageStatsReport\.txt"

# Graph settings
FIGURE_DPI = 300
FIGURE_SIZE = (10, 6)
LINE_STYLES = ['-', '--', '-.', ':']
MARKERS = ['o', 's', '^', 'D', '*', 'x', '+']
COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
          '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

# Metrics of interest with human display names
METRICS = {
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

# Time metrics to convert to seconds (if needed)
TIME_METRICS = ['latency_avg', 'latency_med', 'buffertime_avg', 'buffertime_med']

# Logging settings
LOGGING_LEVEL = "INFO"