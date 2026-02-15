import streamlit as st
import data_processing as dp

st.set_page_config(page_title="Таблиця", page_icon="🗂️")
st.sidebar.header("Таблиця")
geo_data = dp.get_normalize_data()
df_b = dp.get_extended_data(geo_data)
st.write(df_b)