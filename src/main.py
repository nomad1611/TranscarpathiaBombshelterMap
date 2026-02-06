import pandas as pd
import data_processing as dp
from IPython.display import display
import streamlit as st

raw_dataset = dp.get_Bombshelter_info()
geo_data = dp.get_normalize_data()

st.sidebar.header("Filter")
cityName: str = st.sidebar.selectbox(
    "Виберіть місто в якому бажаєте знайти укриття",
    dp.get_cityName(geo_data)
)
typeBombshelter : list = st.sidebar.multiselect("Тип укриття", ["Найпростіші укриття", "ПРУ", "Сховище"], default=["Найпростіші укриття", "ПРУ", "Сховище"] ) 

size : int = st.sidebar.slider(
    "Місткість бомбосховища",
    0, 3000
)
bezbar : bool = st.sidebar.checkbox("Безбарʼєрність")


st.header("Мапа будівель цивільного захисту на території Закарпатської області")
st.write(cityName)
st.map(dp.get_city_info(cityName, geo_data))

 