"""
kpi_display.py

Reusable Streamlit display components for KPI cards and Plotly charts.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


def display_kpi_card(
    title: str,
    kpis: list[int | float | str],
    kpi_names: list[str],
) -> None:
    """Render a styled KPI summary card with multiple metrics.

    Args:
        title: Heading text displayed at the top of the card.
        kpis: Metric values. Integers and floats are formatted with a
            space thousands-separator; strings are displayed as-is.
        kpi_names: Labels that correspond 1-to-1 with *kpis*.
    """
    def _format(value: int | float | str) -> str:
        if isinstance(value, (int, float)):
            return f"{value:,}".replace(",", "\u00a0")  # non-breaking space
        return str(value)

    metrics_html = "".join(
        f"""
        <div style="flex:1; text-align:center; padding:10px;">
            <div style="font-size:14px; color:#d1e7dd; margin-bottom:5px;">{label}</div>
            <div style="font-size:28px; font-weight:bold; color:white;">{_format(value)}</div>
        </div>"""
        for label, value in zip(kpi_names, kpis)
    )

    st.markdown(
        f"""
        <div style="background-color:#255c54; border-radius:15px; padding:20px;
                    box-shadow:0 4px 6px rgba(0,0,0,0.1); margin-bottom:20px;
                    font-family:sans-serif;">
            <h3 style="color:white; margin:0 0 15px 0; padding-bottom:10px;
                       border-bottom:1px solid rgba(255,255,255,0.3);
                       font-size:20px; text-align:left;">
                {title}
            </h3>
            <div style="display:flex; justify-content:space-between; flex-wrap:wrap;">
                {metrics_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def display_pie_chart(
    df_sum: pd.DataFrame,
    color_palette: list[str] | None = None,
    value: str | None = None,
    title: str | None = None,
) -> None:
    """Render a donut pie chart from an aggregated DataFrame.

    Args:
        df_sum: DataFrame whose index contains category labels and
            whose *value* column holds the numeric totals.
        color_palette: Ordered list of hex colour strings.
        value: Column name to use as slice values.
        title: Chart title.
    """
    fig = px.pie(
        df_sum,
        names=df_sum.index,
        values=value,
        title=title,
        color_discrete_sequence=color_palette,
        hole=0.4,
    )
    fig.update_layout(
        title_font_size=24,
        legend=dict(font=dict(size=18), orientation="h", y=-0.1),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    st.plotly_chart(fig, width="stretch")


def display_bar_chart(
    s: pd.Series,
    title: str | None = None,
    color: str | None = None,
    color_palette: list[str] | None = None,
) -> None:
    """Render a horizontal bar chart from a sorted Series.

    Args:
        s: Series with category labels as the index and numeric totals
            as values.  Should already be sorted in the desired order.
        title: Chart title.
        color: Column/field name used to drive continuous colour scale.
        color_palette: Two-colour list used as the continuous scale
            endpoints (e.g. ``["#53a664", "#255c54"]``).
    """
    fig = px.bar(
        s,
        x=s.values,
        y=s.index,
        orientation="h",
        title=title,
        text_auto=True,
        color=s.values,
        color_continuous_scale=color_palette,
        labels={"color": color},
    )
    fig.update_layout(
        title_font_size=24,
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
        coloraxis_showscale=False,
        font=dict(size=18),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    fig.update_traces(textfont_size=16, textposition="outside", cliponaxis=False)
    st.plotly_chart(fig, width="stretch")