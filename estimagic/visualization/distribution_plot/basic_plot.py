"""
Draw interactive distribution plots that allow to identify particular obseservations.

One can think of the interactive distribution plot as a clickable histogram.
The main difference to a histogram is that in this type of plot
every bar is a stack of bricks where each brick identifies a particular observation.
By hovering or clicking on a particular brick you can learn more about that observation
making it easy to identify and analyze patterns.

Estimagic uses interactive distribution plots for two types of visualizations:
1. (static) parameter comparison plots
2. (updating) loglikelihood contribution plots

"""
import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource
from bokeh.models import Title
from bokeh.plotting import figure
from bokeh.plotting import show

from estimagic.logging.create_database import load_database
from estimagic.visualization.distribution_plot.callbacks import add_single_plot_tools
from estimagic.visualization.distribution_plot.callbacks import (
    add_value_slider_in_front,
)
from estimagic.visualization.distribution_plot.callbacks import create_group_widgets
from estimagic.visualization.distribution_plot.callbacks import create_view
from estimagic.visualization.distribution_plot.histogram_columns import (
    add_histogram_columns_to_tidy_df,
)


def interactive_distribution_plot(
    source,
    value_col,
    id_col,
    group_cols=None,
    subgroup_col=None,
    lower_bound_col=None,
    upper_bound_col=None,
    figure_height=None,
    width=500,
    x_padding=0.1,
    num_bins=50,
    axis_for_every_parameter=False,
):
    """Create an interactive distribution plot from a tidy DataFrame.

    Args:
        source (pd.DataFrame or str or pathlib.Path):
            Tidy DataFrame or location of the database file that contains tidy data.
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
        subgroup_col (str, optional):
            Name of a column according to whose values individual bricks will be
            color coded. The selection which column is the subgroup_col
            can be changed in the plot from a dropdown menu.
        lower_bound_col (str, optional):
            Name of the column identifying the lower bound of the whisker.
        upper_bound_col (str, optional):
            Name of the column identifying the upper bound of the whisker.
        figure_height (int, optional):
            height of the figure (i.e. of all plots together, in pixels).
        width (int, optional):
            width of the figure (in pixels).
        x_padding (float, optional):
            the x_range is extended on each side by this factor of the range of the data
        num_bins (int, optional):
            number of bins
        axis_for_every_parameter (bool, optional):
            if False the x axis is only shown once for every group of parameters.

    Returns:
        source (bokeh.models.ColumnDataSource): data underlying the plots
        gridplot (bokeh.layouts.Column): grid of the distribution plots.

    """
    if group_cols is None:
        group_cols = []
    elif isinstance(group_cols, str):
        group_cols = [group_cols]

    if isinstance(source, pd.DataFrame):
        df = source
    elif isinstance(source, Path) or isinstance(source, str):
        assert os.path.exists(
            source
        ), "The path {} you specified does not exist.".format(source)
        database = load_database(path=source)  # noqa
        raise NotImplementedError("Databases not supported yet.")

    hist_data = add_histogram_columns_to_tidy_df(
        df=df,
        group_cols=group_cols,
        value_col=value_col,
        subgroup_col=subgroup_col,
        id_col=id_col,
        num_bins=num_bins,
        x_padding=x_padding,
    )

    plot_height = _determine_plot_height(
        figure_height=figure_height, data=hist_data, group_cols=group_cols,
    )

    source, plots = _create_plots(
        df=hist_data,
        value_col=value_col,
        group_cols=group_cols,
        subgroup_col=subgroup_col,
        id_col=id_col,
        lower_bound_col=lower_bound_col,
        upper_bound_col=upper_bound_col,
        plot_height=plot_height,
        width=width,
        axis_for_every_parameter=axis_for_every_parameter,
    )
    grid = gridplot(plots, toolbar_location="right", ncols=1)
    show(grid)
    return source, plots


# =====================================================================================
#                                    PLOT FUNCTIONS
# =====================================================================================


def _create_plots(
    df,
    value_col,
    group_cols,
    subgroup_col,
    id_col,
    lower_bound_col,
    upper_bound_col,
    plot_height,
    width,
    axis_for_every_parameter,
):
    source = ColumnDataSource(df)

    plots = create_group_widgets(source=source, subgroup_col=subgroup_col)

    # =====================================================

    if len(group_cols) == 0:
        gb = [(None, df)]
        plots.append(title_fig(group_type="All Parameters", group_name=""))
        old_group_tup = None
    elif len(group_cols) == 1:
        old_group_tup = tuple([np.nan] * len(group_cols))
        gb = df.groupby(group_cols[0])
        plots.append(title_fig(group_type=group_cols[0], group_name=""))

    else:
        gb = df.groupby(group_cols)
        old_group_tup = tuple([np.nan] * len(group_cols))

    for group_tup, group_df in gb:
        plots, new_group, old_group_tup = _check_and_handle_group_switch(
            group_cols=group_cols,
            old_group_tup=old_group_tup,
            group_tup=group_tup,
            plots=plots,
        )

        view = create_view(
            source=source,
            group_df=group_df,
            subgroup_col=subgroup_col,
            widget=plots[0],
        )

        plot_title = _plot_title(group_cols, group_tup)

        param_plot = _create_base_plot(
            title=plot_title,
            group_df=group_df,
            source=source,
            view=view,
            plot_height=plot_height,
            width=width,
            id_col=id_col,
        )

        param_plot = _add_ci_bars_if_present(
            param_plot=param_plot,
            source=source,
            view=view,
            lower_bound_col=lower_bound_col,
            upper_bound_col=upper_bound_col,
        )

        _style_plot(
            fig=param_plot,
            new_group=new_group,
            axis_for_every_parameter=axis_for_every_parameter,
        )

        plots.append(param_plot)

    plots = add_value_slider_in_front(
        df=df,
        value_col=value_col,
        lower_bound_col=lower_bound_col,
        upper_bound_col=upper_bound_col,
        plots=plots,
    )
    return source, plots


def _check_and_handle_group_switch(group_cols, old_group_tup, group_tup, plots):
    if len(group_cols) < 2:
        new_group = False
    else:
        new_group = old_group_tup[:-1] != group_tup[:-1]
        if new_group:
            plots = _write_titles(
                plots=plots,
                group_cols=group_cols,
                old_group_tup=old_group_tup,
                group_tup=group_tup,
            )
            old_group_tup = group_tup
    return plots, new_group, old_group_tup


def _plot_title(group_cols, group_tup):
    if len(group_cols) == 0:
        plot_title = ""
    elif len(group_cols) == 1:
        plot_title = str(group_tup)
    else:
        plot_title = "{} {}".format(group_cols[-1], group_tup[-1])
    return plot_title.title()


def _create_base_plot(title, group_df, source, view, plot_height, width, id_col):
    x_range = group_df["xmin"].unique()[0], group_df["xmax"].unique()[0]
    param_plot = figure(
        title=title,
        plot_height=plot_height,
        plot_width=width,
        tools="reset,save",
        y_axis_location="left",
        x_range=x_range,
    )
    point_glyph = param_plot.rect(
        source=source,
        view=view,
        x="binned_x",
        width="rect_width",
        y="dodge",
        height=1,
        color="color",
        selection_color="color",
        nonselection_color="color",
        alpha=0.5,
        selection_alpha=0.7,
        nonselection_alpha=0.1,
    )

    param_plot = add_single_plot_tools(param_plot, point_glyph, source, id_col)
    return param_plot


def _add_ci_bars_if_present(param_plot, source, view, lower_bound_col, upper_bound_col):
    if lower_bound_col is not None and upper_bound_col is not None:
        param_plot.hbar(
            source=source,
            view=view,
            y="dodge",
            left=lower_bound_col,
            right=upper_bound_col,
            height=0.01,
            alpha=0.0,
            selection_alpha=0.7,
            nonselection_alpha=0.0,
            color="color",
            selection_color="color",
            nonselection_color="color",
        )
    return param_plot


# =====================================================================================
#                                   STYLING FUNCTIONS
# =====================================================================================


def _determine_plot_height(figure_height, data, group_cols):
    """Calculate the height alloted to each plot in pixels.

    Args:
        figure_height (int): height of the entire figure in pixels
        data (pd.DataFrame): DataFrame of the

    Returns:
        plot_height (int): Plot height in pixels.

    """
    if figure_height is None:
        figure_height = int(max(min(30 * data["dodge"].max(), 1000), 100))

    if len(group_cols) > 1:
        n_groups = len(data.groupby(group_cols[:-1]))
        n_plots = len(data.groupby(group_cols))
    elif len(group_cols) == 1:
        n_groups = 0
        n_plots = len(data.groupby(group_cols))
    else:
        n_groups = 0
        n_plots = 1
    space_of_titles = n_groups * 50
    available_space = figure_height - space_of_titles
    plot_height = int(available_space / n_plots)
    if plot_height < 20:
        warnings.warn(
            "The figure height you specified results in very small ({}) ".format(
                plot_height
            )
            + "plots which may not render well. Adjust the figure height "
            "to a larger value or set it to None to get a larger plot. "
            "Alternatively, you can click on the Reset button "
            "on the right of the plot and your plot should render correctly."
        )
    return plot_height


def _style_plot(fig, new_group, axis_for_every_parameter):
    _style_x_axis(
        fig=fig, new_group=new_group, axis_for_every_parameter=axis_for_every_parameter
    )
    _style_y_axis(fig=fig)

    fig.title.vertical_align = "top"
    fig.title.text_alpha = 70
    fig.title.text_font_style = "normal"
    fig.outline_line_color = None
    fig.min_border_top = 20
    fig.min_border_bottom = 20
    fig.xgrid.visible = False
    fig.ygrid.visible = False
    fig.sizing_mode = "scale_width"


def _style_x_axis(fig, new_group, axis_for_every_parameter):
    if not axis_for_every_parameter:
        if new_group:
            fig.xaxis.visible = False
        else:
            fig.xaxis.axis_line_color = None
        xmin = fig.x_range.start
        xmax = fig.x_range.end
        fig.line([xmin, xmax], [0, 0], line_color="black")
    fig.xaxis.minor_tick_line_color = None


def _style_y_axis(fig):
    fig.yaxis.minor_tick_line_color = None
    fig.yaxis.axis_line_color = None
    fig.yaxis.major_tick_line_color = None


def title_fig(group_type, group_name, width=500, level=0):
    title = Title(
        text="{group_type} {group_name}".format(
            group_type=str(group_type).title(), group_name=str(group_name).title()
        ),
        align="center",
        text_font_size="{}pt".format(15 - 2 * level),
    )
    fig = figure(title=title, plot_height=50, plot_width=width, tools="reset,save",)
    fig.line([], [])  # add renderer to avoid warning
    fig.ygrid.visible = False
    fig.xgrid.visible = False
    fig.outline_line_color = None
    fig.yaxis.axis_line_color = None
    fig.xaxis.axis_line_color = None

    return fig


def _write_titles(plots, group_cols, old_group_tup, group_tup):
    for level in range(len(group_cols) - 1):
        old_name = old_group_tup[level]
        new_name = group_tup[level]
        if old_name != new_name:
            plots.append(title_fig(group_cols[level], new_name, level=level))
    return plots
