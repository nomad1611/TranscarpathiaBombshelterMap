import pandas as pd
import data_processing as dp
from IPython.display import display
import streamlit as st

raw_dataset = dp.get_Bombshelter_info()
geo_data = dp.get_normalize_data()
#display(raw_dataset)
print("*normalize data:*")
st.header("Таблиця всіх будівель цивільного захисту на території Закарпатської області")
st.dataframe(geo_data)

st.write("Укриття Мукачівської громади")
st.map(geo_data)

 