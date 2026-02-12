import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import os

# Visual Standard Colors (Document Mode - White Background)
COLOR_BG = "#FFFFFF" # White
COLOR_TEXT = "#003366" # Navy Blue
COLOR_AXIS = "#003366" # Navy Blue
COLOR_GRID = "#CCCCCC" # Light Grey
COLOR_ACCENT = "#003366" # Navy Blue
COLOR_NEUTRAL = "#95A5A6" # Cool Grey

# Chart Specifics
COLOR_SUCCESS = "#003366" # Navy Blue for primary bars
COLOR_DANGER = "#95A5A6" # Grey for secondary bars

def set_style():
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
    plt.rcParams['text.color'] = COLOR_TEXT
    plt.rcParams['axes.labelcolor'] = COLOR_TEXT
    plt.rcParams['xtick.color'] = COLOR_AXIS
    plt.rcParams['ytick.color'] = COLOR_AXIS
    plt.rcParams['axes.edgecolor'] = COLOR_GRID
    plt.rcParams['axes.spines.top'] = False
    plt.rcParams['axes.spines.right'] = False
    plt.rcParams['axes.spines.left'] = False
    plt.rcParams['axes.spines.bottom'] = True
    plt.rcParams['figure.facecolor'] = COLOR_BG
    plt.rcParams['axes.facecolor'] = COLOR_BG

def generate_sanitization_chart(data, output_path):
    """
    Generates a Diverging Bar Chart.
    Data format: { "category": [...], "values": [...], "colors": [...] }
    """
    set_style()
    fig, ax = plt.subplots(figsize=(6, 3))
    
    categories = data.get("category", [])
    values = data.get("values", [])
    # Default to Orange vs Grey if no colors provided
    bar_colors = data.get("colors", [COLOR_SUCCESS, COLOR_DANGER])
    
    y_pos = np.arange(len(categories))
    
    ax.barh(y_pos, values, align='center', color=bar_colors)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(categories)
    ax.invert_yaxis()  # labels read top-to-bottom
    ax.set_xlabel('Sentiment Score')
    ax.axvline(0, color=COLOR_NEUTRAL, linewidth=0.8)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, transparent=False) # Transparent=False to keep black bg
    plt.close()
    return output_path

def generate_waterfall_chart(data, output_path):
    """
    Generates a Waterfall Chart for Sentiment Velocity.
    Data format: { "stages": [...], "values": [...] }
    """
    set_style()
    fig, ax = plt.subplots(figsize=(6, 3))
    
    stages = data.get("stages", [])
    values = data.get("values", [])
    
    # Calculate step positions
    running_total = 0
    indices = range(len(stages))
    
    # Simplified waterfall logic re-integrated/cleaned from previous version
    current_lev = 0
    for i, val in enumerate(values):
        is_total = (i == 0) or (i == len(values) - 1)
        
        if is_total:
            ax.bar(stages[i], val, color=COLOR_NEUTRAL) # White/Grey for Start/End
            current_lev = val
        else:
            # Change
            height = abs(val)
            bottom = current_lev if val < 0 else current_lev
            # Use Orange for drops (attention needed) or Gains?
            # Let's use Orange for everything 'active'
            color = COLOR_ACCENT 
            ax.bar(stages[i], height, bottom=bottom if val < 0 else current_lev, color=color)
            current_lev += val

    ax.set_ylabel('Sentiment Score')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, transparent=False)
    plt.close()
    return output_path
