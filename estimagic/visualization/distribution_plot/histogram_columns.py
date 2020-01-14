"""Functions to calculate the necessary information to plot the histogram."""
from functools import partial

import numpy as np
import pandas as pd

from estimagic.dashboard.plotting_functions import get_color_palette


def add_histogram_columns_to_tidy_df(
    df, group_cols, subgroup_col, value_col, id_col, num_bins, x_padding
):
    """Add bin, rectangle width, vertical position and color as columns to a DataFrame.

    Args:
        df (pd.DataFrame):
            Tidy DataFrame.
            see: http://vita.had.co.nz/papers/tidy-data.pdf
        value_col (str):
            Name of the column for which to draw the histogram.
            In case of a parameter comparison plot this would be the "value" column
            of the params DataFrame returned by maximize or minimize.
        id_col (str):
            Name of the column that identifies
            which values belong to the same observation.
            In case of a parameter comparison plot
            this would be the "model_name" column.
        group_cols (list):
            Name of the columns that identify groups that will be plotted together.
            In case of a parameter comparison plot this would be the parameter group
            and parameter name.
        subgroup_col (str):
            Name of a column according to whose values individual bricks will be
            color coded. The selection which column is the subgroup_col
            can be changed in the plot from a dropdown menu.
        x_padding (float):
            the x_range is extended on each side by this factor of the range of the data
        num_bins (int):
            number of bins
    """

    drop_and_sort_cols = group_cols.copy()
    if subgroup_col is not None:
        drop_and_sort_cols.append(subgroup_col)
    drop_and_sort_cols += [value_col, id_col]
    hist_data = df.dropna(subset=drop_and_sort_cols, how="any").copy()
    hist_data.sort_values(drop_and_sort_cols, inplace=True)
    drop_index = (hist_data.index == range(len(hist_data))).all()
    if hist_data.index.name is None:
        new_index_name = "_index_{}"
        i = 0
        while new_index_name.format(i) in hist_data.columns:
            i += 1
        hist_data.index.name = new_index_name.format(i)
    hist_data.reset_index(inplace=True, drop=drop_index)
    hist_data[["binned_x", "rect_width"]] = _bin_width_and_midpoints(
        df=hist_data,
        group_cols=group_cols,
        value_col=value_col,
        num_bins=num_bins,
        x_padding=x_padding,
    )

    hist_data["dodge"] = 0.5 + hist_data.groupby(group_cols + ["binned_x"]).cumcount()
    if subgroup_col is not None:
        hist_data[subgroup_col] = _clean_subgroup_col(sr=hist_data[subgroup_col])
        hist_data["color"] = _create_color_col(sr=hist_data[subgroup_col])
    else:
        hist_data["color"] = "#035096"
    return hist_data


def _bin_width_and_midpoints(df, group_cols, value_col, num_bins, x_padding):
    bin_width_and_midpoint_func = partial(
        _bin_width_and_midpoints_per_group,
        value_col=value_col,
        num_bins=num_bins,
        x_padding=x_padding,
    )
    if len(group_cols) > 1:
        # Exclude the last column because the last column identifies the plot
        # but we want the bins to be comparable across plots of the same (sub)group.
        grouped = df.groupby(group_cols[:-1])
        return grouped.apply(bin_width_and_midpoint_func)
    else:
        # if no or just one group_col is given
        return bin_width_and_midpoint_func(df)


def _bin_width_and_midpoints_per_group(df, value_col, num_bins, x_padding):
    xmin, xmax = _calculate_x_bounds(df, value_col, x_padding)
    bins, rect_width = np.linspace(
        start=xmin, stop=xmax, num=num_bins + 1, retstep=True
    )
    midpoints = bins[:-1] + rect_width / 2
    values_midpoints = pd.cut(df[value_col], bins, labels=midpoints).astype(float)
    to_add = values_midpoints.to_frame(name="binned_x")
    to_add["rect_width"] = rect_width
    return to_add


def _calculate_x_bounds(df, value_col, padding):
    raw_min = df[value_col].min()
    raw_max = df[value_col].max()
    white_space = (raw_max - raw_min).clip(1e-50) * padding
    x_min = raw_min - white_space
    x_max = raw_max + white_space
    return x_min, x_max


def _clean_subgroup_col(sr):
    if len(sr.unique()) < 10:
        sr = sr.astype(str)
    else:
        try:
            sr = sr.astype(float)
        except ValueError:
            sr = sr.astype(str)
    return sr


def _create_color_col(sr):
    subgroup_vals = sr.unique()
    palette = get_color_palette(len(subgroup_vals))
    color_dict = {val: color for val, color in zip(subgroup_vals, palette)}
    return sr.replace(color_dict)