import pandas as pd
import data_processing as dp
from IPython.display import display
import streamlit as st
import os
import leafmap.foliumap as leafmap

geo_data = dp.get_normalize_data()
st.write(geo_data)
m = leafmap.Map(center=[48.63176, 24.2], zoom=8)

m.add_basemap('HYBRID')
m.add_basemap('Stadia.StamenTerrainLines')
m.add_basemap('Stadia.StamenTerrainLabels')
m.add_basemap('Stadia.OSMBright',False)






m.add_points_from_xy(
   geo_data,
  x = 'longitude',
  y='latitude',
  popup=['properties.Name', 'properties.OTG', 'properties.City', 'properties.Adress','properties.Type','properties.People', 'properties.Bezbar'], 
  
    
  )

m.to_streamlit()

#display(geo_data["properties.Adress"].drop_duplicates())
#s = dp.clean_properties_Adress(geo_data['properties.Adress'])
#s = s.drop_duplicates()
#display(s.sort_values(ascending=True).to_string())

#st.sidebar.header("Filter")
#cityName: str = st.sidebar.selectbox(
  #  "Виберіть місто в якому бажаєте знайти укриття",
 #   dp.get_cityName(geo_data)
#)
#typeBombshelter : list = st.sidebar.multiselect("Тип укриття", ["Найпростіші укриття", "ПРУ", "Сховище"], default=["Найпростіші укриття", "ПРУ", "Сховище"] ) 

#size : int = st.sidebar.slider(
 #   "Місткість бомбосховища",
  #  0, 3000
#)
#bezbar : bool = st.sidebar.checkbox("Безбарʼєрність")


#st.header("Мапа будівель цивільного захисту на території Закарпатської області")
#st.write(cityName)
#st.map(dp.get_city_info(cityName, geo_data))

 