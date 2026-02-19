"""
Main.py

Streamlit entry point: interactive map and analytics dashboard for
civil-defence shelters in Transcarpathia.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
import leafmap.foliumap as leafmap

import data_processing as dp
import kpi_display as kd

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Головна сторінка", page_icon="🏠", layout="wide")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.header("Головна сторінка")
st.markdown(
    "<p style='font-size:20px;'>"
    "<b>Тема:</b> Інформаційно-аналітична система контролю та візуалізації "
    "будівель цивільного захисту на території Закарпатської області"
    "</p>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='font-size:20px;'>"
    "<b>Мета:</b> Процес обробки та візуалізації геопросторових даних про захисні "
    "споруди Закарпатської області, отриманих з відкритого регіонального порталу даних"
    "</p>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Data loading  (both raw + extended needed for different operations)
# ---------------------------------------------------------------------------

geo_data = dp.get_normalized_data()

if geo_data is None:
    st.error("Не вдалося завантажити дані. Спробуйте оновити сторінку.")
    st.stop()

df_display = dp.get_extended_data(geo_data)

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------

st.sidebar.title("Фільтр та Пошук")

otg_options: list[str] = [" "] + dp.get_sorted_column_values(df_display["ОТГ"])
selected_otg: str = st.sidebar.selectbox("ОТГ (об'єднана територіальна громада)", otg_options)

city_options: list[str] = dp.get_city_options(selected_otg, geo_data)
selected_city: str = st.sidebar.selectbox("Населений пункт", city_options)

all_types: list[str] = dp.get_sorted_column_values(df_display["Тип"])
selected_types: list[str] = st.sidebar.multiselect("Тип укриття", all_types, default=all_types)

max_capacity: int = st.sidebar.slider("Місткість бомбосховища", 0, 3_876, 3_876, 10)

accessible_only: bool = st.sidebar.checkbox("Безбар'єрність")

# ---------------------------------------------------------------------------
# Map
# ---------------------------------------------------------------------------

st.subheader("Мапа")

map_ = leafmap.Map(center=[48.63176, 24], zoom=8)
map_.add_basemap("HYBRID")
map_.add_basemap("Stadia.StamenTerrainLines")
map_.add_basemap("Stadia.StamenTerrainLabels")
map_.add_basemap("Stadia.OSMBright", False)

df_filtered = dp.search_data(
    df_display,
    city_name=selected_city,
    otg_name=selected_otg,
    shelter_type=selected_types,
    max_capacity=max_capacity,
    accessible_only=accessible_only,
)
df_filtered = df_filtered.copy()
df_filtered["ID"] = df_filtered.index

map_.add_points_from_xy(
    df_filtered,
    x="longitude",
    y="latitude",
    popup=[
        "ID",
        "Назва",
        "ОТГ",
        "Населений пункт",
        "Адреса",
        "Тип",
        "Місткість",
        "Інклюзивність",
        "Посилання",
    ],
)
map_.to_streamlit()

# ---------------------------------------------------------------------------
# KPI card
# ---------------------------------------------------------------------------

shelter_count: int = len(df_filtered)
total_capacity: int = int(df_filtered["Місткість"].sum())

if shelter_count > 0:
    accessibility_pct = (
        df_filtered["Інклюзивність"].value_counts(normalize=True).get("Так", 0) * 100
    )
else:
    accessibility_pct = 0.0

kd.display_kpi_card(
    title="Аналітичні дані",
    kpis=[shelter_count, total_capacity, f"{accessibility_pct:,.1f}%"],
    kpi_names=["Кількість бомбосховищ", "Загальна місткість", "Рівень інклюзивності"],
)

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

col_left, col_right = st.columns(2)
PIE_PALETTE = ["#255c54", "#3d814b", "#8f9e21", "#ffa600"]
BAR_PALETTE = ["#53a664", "#255c54"]
CAPACITY_COL = "Місткість"

with col_left:
    type_capacity = df_filtered.groupby("Тип")[CAPACITY_COL].sum().to_frame()
    kd.display_pie_chart(
        type_capacity,
        color_palette=PIE_PALETTE,
        value=CAPACITY_COL,
        title="Розподіл місткості за типом",
    )

with col_right:
    # Determine the relevant OTG for the bar chart scope
    target_otg: str | None = None
    if selected_otg != " ":
        target_otg = selected_otg
    elif selected_city != " ":
        match = df_display.loc[df_display["Населений пункт"] == selected_city, "ОТГ"]
        target_otg = match.iloc[0] if not match.empty else None

    if target_otg:
        df_chart_source = df_display[df_display["ОТГ"] == target_otg]
        bar_title = f"Топ-5: {target_otg} громада"
        top_n = 5
    else:
        df_chart_source = df_display
        bar_title = "Топ-10: Закарпатська обл."
        top_n = 10

    city_capacity = (
        df_chart_source.groupby("Населений пункт")[CAPACITY_COL]
        .sum()
        .sort_values(ascending=True)
        .tail(top_n)
    )
    kd.display_bar_chart(city_capacity, title=bar_title, color=CAPACITY_COL, color_palette=BAR_PALETTE)