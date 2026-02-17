import pandas as pd
import data_processing as dp
from IPython.display import display
import streamlit as st
import leafmap.foliumap as leafmap
import plotly.express as px

st.set_page_config(page_title="Головна сторінка", page_icon="🏠", layout="wide")

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

type_sum = pd.DataFrame(df_point.groupby("Тип")["Місткість"].sum())
pie_palette =["#255c54","#3d814b","#8f9e21","#ffa600"]
pie_chart = px.pie(type_sum, names=type_sum.index,
        values = "Місткість",
         title="Розподіл місткості бомбосховищ за типом укриття",
         color_discrete_sequence=pie_palette,
         hole=0.4
         )
pie_chart.update_layout(
    title=dict(
        text="Розподіл місткості бомбосховищ за типом укриття",
        font=dict(size=30)
    ),
    
    # 2. The Legend (Right side items)
    legend=dict(
        font=dict(size=25), # <--- THIS is what changes the text size
        orientation="v",    # "v" for vertical list, "h" for horizontal
        yanchor="top",      # Anchor to top
        y=1,                # Position at top
        xanchor="left",     # Anchor to left
        x=1.05              # Move slightly to the right of the chart
    ),
    
    # 3. Global font (Backup for other text)
    font=dict(size=20)
)

st.plotly_chart(pie_chart, height="stretch")

# 1. Determine the "Target OTG" for the chart context
target_otg = None

if OTGName != " ":
    # Case A: User explicitly selected an OTG
    target_otg = OTGName
elif cityName != " ":
    # Case B: User skipped OTG but selected a City
    # We find the OTG that this city belongs to
    # .values[0] grabs the string value from the series
    target_otg = df_b[df_b['Населений пункт'] == cityName]['ОТГ'].values[0]

# 2. Prepare Data for the Chart (Separate from the Map data!)
if target_otg:
    # Filter the FULL dataset to get all cities in this OTG
    df_chart = df_b[df_b['ОТГ'] == target_otg]
    title = f"Топ-5 нас. пунктів за місткістю будівель цивільного захисту: {target_otg} громада"
    top_n = 5
else:
    # Case C: Nothing selected, show the whole region
    df_chart = df_b
    title = "Топ-10 нас. пунктів Закарпатської обл. за місткістю будівель цивільного захисту"
    top_n = 10

# 3. Group and Sort
# We calculate total capacity per city
df_citySize = (
    df_chart.groupby("Населений пункт")["Місткість"]
    .sum()
    .sort_values(ascending=True) # Sort so largest is at the end (top of horiz chart)
    .tail(top_n) # Take the top N largest
)

# 4. Plot
fig = px.bar(
    df_citySize, 
    x=df_citySize.values, 
    y=df_citySize.index, 
    orientation="h", 
    title=title,
    text_auto=True,
    labels={'x': 'Загальна місткість (осіб)', 'y': 'Населений пункт'},
    color='Місткість',
    # Use a built-in green scale or make a custom one
    color_continuous_scale=["#53a664", "#255c54"]
    
)


# Update the global font settings
fig.update_layout(
    title_font_size=30,
    xaxis_title_font_size=25,
    font=dict(
         # Optional: Change font family
        size=25,         # Set base font size (Default is usually 12)
        #color="black"
    )
)
fig.update_traces(textfont_size=30,      # Size of the numbers on the bars
    textposition='outside')


st.plotly_chart(fig, height="stretch")


 