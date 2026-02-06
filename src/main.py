import pandas as pd
import data_processing as dp
from IPython.display import display
import streamlit as st

raw_dataset = dp.get_Bombshelter_info()
geo_data = dp.get_normalize_data()
#display(raw_dataset)

#st.header("Таблиця всіх будівель цивільного захисту на території Закарпатської області")
#st.dataframe(geo_data)
cityName = st.sidebar.selectbox(
    "Виберіть місто в якому бажаєте знайти укриття",
    dp.get_cityName(geo_data)
)
st.header("Мапа будівель цивільного захисту на території Закарпатської області")
st.write(cityName)
st.map(dp.get_city_info(cityName, geo_data))

 