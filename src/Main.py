import pandas as pd
import data_processing as dp
from IPython.display import display
import streamlit as st
import leafmap.foliumap as leafmap

st.set_page_config(page_title="Головна сторінка")

st.header("Головна сторінка")
st.write("Інформаційно-аналітична система контролю та візуалізації будівель цивільного захисту на території Закарпатської області")
st.subheader("Мапа")
geo_data = dp.get_normalize_data()
df_b = dp.get_extended_data(geo_data)
#st.write(df_b)



m = leafmap.Map(center=[48.63176, 24.2], zoom=8)

m.add_basemap('HYBRID')
m.add_basemap('Stadia.StamenTerrainLines')
m.add_basemap('Stadia.StamenTerrainLabels')
m.add_basemap('Stadia.OSMBright',False)

df_b['ID']=df_b.index
m.add_points_from_xy(
   df_b,
  x = 'longitude',
  y = 'latitude',
  popup=['ID','Назва', 'ОТГ', 'Населений пункт', 'Адреса','Тип','Місткість', 'Інклюзивність','Посилання'], 
  
    
  )

m.to_streamlit()

st.sidebar.header("Головна сторінка")
st.sidebar.header("Filter")
cityName: str = st.sidebar.selectbox(
    "Виберіть місто в якому бажаєте знайти укриття",
    dp.get_sorted_columnData("Населений пункт", df_b)
)
Type = dp.get_sorted_columnData('Тип', df_b)
typeBombshelter : list = st.sidebar.multiselect("Тип укриття", Type, default = Type ) 

#size : int = st.sidebar.slider(
 #   "Місткість бомбосховища",
  #  0, 3000
#)
bezbar : bool = st.sidebar.checkbox("Безбарʼєрність")


#st.header("Мапа будівель цивільного захисту на території Закарпатської області")
#st.write(cityName)
#st.map(dp.get_city_info(cityName, geo_data))

 