import pandas as pd
import data_processing as dp
import streamlit as st
import leafmap.foliumap as leafmap
import kpi_display as kd

st.set_page_config(page_title="Головна сторінка", page_icon="🏠", layout="wide")

st.header("Головна сторінка")
#st.write("Інформаційно-аналітична система контролю та візуалізації будівель цивільного захисту на території Закарпатської області")
st.markdown(
    '<p style="font-size: 20px;"> <b>Тема:</b>  Інформаційно-аналітична система контролю та візуалізації будівель цивільного захисту на території Закарпатської області</p>',unsafe_allow_html=True )
st.markdown('<p style="font-size: 20px;"> <b>Мета:</b> Процес обробки та візуалізації геопросторових даних про захисні споруди Закарпатської області, отриманих з відкритого регіонального порталу даних</p>',unsafe_allow_html=True)
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

SumShelter = df_point["ID"].count()
SumSize = df_point["Місткість"].sum()

# 2. Safe calculation for Accessibility %
if len(df_point) > 0:
    counts = df_point["Інклюзивність"].value_counts(normalize=True) * 100
    bezbar_val = counts.get("Так", 0) # Get "Так" or return 0
else:
    bezbar_val = 0

bezbar_str = f"{bezbar_val:,.1f}%"
kd.display_kpi_card(
    "Аналітичні дані", 
    [SumShelter, SumSize, bezbar_str], 
    ["Кількість бомбосховищ", "Загальна місткість", "Рівень інклюзивності"]
)
col1, col2 = st.columns(2)
color='Місткість'
# --- LEFT COLUMN: PIE CHART ---
with col1:
    type_sum = pd.DataFrame(df_point.groupby("Тип")["Місткість"].sum())
    pie_palette = ["#255c54", "#3d814b", "#8f9e21", "#ffa600"]
    
    kd.display_pie_chart(type_sum, pie_palette,color,"Розподіл місткості за типом")
    

# --- RIGHT COLUMN: BAR CHART ---
with col2:
    # 1. Logic for Bar Chart Title & Data
    target_otg = None
    if OTGName != " ":
        target_otg = OTGName
    elif cityName != " ":
        # Safety check: ensure we actually find an OTG
        found_otg = df_b[df_b['Населений пункт'] == cityName]['ОТГ'].values
        target_otg = found_otg[0] if len(found_otg) > 0 else None

    if target_otg:
        df_chart = df_b[df_b['ОТГ'] == target_otg]
        title_bar = f"Топ-5: {target_otg} громада"
        top_n = 5
    else:
        df_chart = df_b
        title_bar = "Топ-10: Закарпатська обл."
        top_n = 10

    # 2. Group and Sort
    df_citySize = (
        df_chart.groupby("Населений пункт")["Місткість"]
        .sum()
        .sort_values(ascending=True)
        .tail(top_n)
    )

    kd.display_bar_chart(df_citySize, title_bar, color, ["#53a664", "#255c54"])