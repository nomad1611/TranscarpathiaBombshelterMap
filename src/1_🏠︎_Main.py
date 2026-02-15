import pandas as pd
import data_processing as dp
from IPython.display import display
import streamlit as st
import leafmap.foliumap as leafmap

st.set_page_config(page_title="Головна сторінка", page_icon="🏠")

st.header("Головна сторінка")
st.write("Інформаційно-аналітична система контролю та візуалізації будівель цивільного захисту на території Закарпатської області")
st.subheader("Мапа")

geo_data = dp.get_normalize_data()
df_b = dp.get_extended_data(geo_data)




st.sidebar.title("Фільтр та Пошук")

otg_options = [" "] + dp.get_sorted_columnData(df_b["ОТГ"])
OTGName: str = st.sidebar.selectbox(
    "ОТГ(об'єднана територіальна громада)",
    otg_options
)


city_options = dp.get_city_info(OTGName, geo_data)
cityName: str = st.sidebar.selectbox(
    "Населений пункт",
    city_options
)


Type = dp.get_sorted_columnData(df_b['Тип'])
typeBombshelter : list = st.sidebar.multiselect("Тип укриття", Type, default = Type ) 


size : int = st.sidebar.slider(
   "Місткість бомбосховища",
  0, 3876, 3876, 10
)

bezbar : bool = st.sidebar.checkbox("Безбарʼєрність")


m = leafmap.Map(center = [48.63176, 24], zoom = 8)

m.add_basemap('HYBRID')
m.add_basemap('Stadia.StamenTerrainLines')
m.add_basemap('Stadia.StamenTerrainLabels')
m.add_basemap('Stadia.OSMBright',False)


df_point = dp.search_data(
    df_b,
    cityName,
    OTGName,
    typeBombshelter,
    size,  
    bezbar
    )
df_point['ID'] = df_point.index

m.add_points_from_xy(
   df_point,
  x = 'longitude',
  y = 'latitude',
  popup=['ID','Назва', 'ОТГ', 'Населений пункт', 'Адреса','Тип','Місткість', 'Інклюзивність','Посилання'], 
)

m.to_streamlit()


def display_kpi_metrics(kpis: list[float], kpi_names: list[str]):
    st.header("Аналітичні дані")
    for i, (col, (kpi_name, kpi_value)) in enumerate(zip(st.columns(4), zip(kpi_names, kpis))):
        col.metric(label=kpi_name, value=kpi_value)

SumShelter = len(df_point)
SumSize = df_point["Місткість"].sum()
s_bezbar = df_point["Інклюзивність"].value_counts(normalize=True)*100
bezbar = f"{s_bezbar.loc["Так"]:,.2f}%"
list_metrics = [SumShelter, SumSize, bezbar]
list_labels = ["Загальна к-сть бомбосховищ", "Загальна місткість", "Рівень інклюзивності"]

display_kpi_metrics(list_metrics, list_labels)
#st.metric("Загальна к-сть бомбосховищ", len(df_point))
#st.metric("Загальна місткість", df_point["Місткість"].sum())
#s_bezbar = df_point["Інклюзивність"].value_counts(normalize=True)*100
#bezbar = f"{s_bezbar.loc["Так"]:,.2f}%"
#st.metric("Рівень інклюзивності", bezbar )


 