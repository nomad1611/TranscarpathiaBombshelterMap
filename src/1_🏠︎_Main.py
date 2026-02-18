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


def display_kpi_card(title: str, kpis: list, kpi_names: list[str]):
    # 1. Generate the inner HTML for metrics
    metrics_html = ""
    for label, value in zip(kpi_names, kpis):
        
        # Formatting Logic:
        # If it's a number (int/float), add commas (e.g., 271,538)
        # If it's a string (like "16.2%"), leave it alone
        if isinstance(value, (int, float)):
            formatted_value = f"{value:,}".replace(",", " ") # Use space as thousands separator
        else:
            formatted_value = value
            
        metrics_html += f"""
<div style="flex: 1; text-align: center; padding: 10px;">    <div style="font-size: 14px; color: #d1e7dd; margin-bottom: 5px;">{label}</div> <div style="font-size: 28px; font-weight: bold; color: white;">{formatted_value}</div> </div>"""
        
    # 2. Render the Main Card Container
    # FIX: Removed indentation inside the f-string here too
    st.markdown(f"""
<div style="background-color: #255c54; border-radius: 15px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; font-family: sans-serif;">
<h3 style="color: white; margin: 0 0 15px 0; padding-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.3); font-size: 20px; text-align: left;">        
{title}</h3>
<div style="display: flex; justify-content: space-between; flex-wrap: wrap;">
{metrics_html}
</div>
</div>
""", unsafe_allow_html=True)
    # Use the new parameter
SumShelter = df_point["ID"].count()
SumSize = df_point["Місткість"].sum()

# 2. Safe calculation for Accessibility %
if len(df_point) > 0:
    counts = df_point["Інклюзивність"].value_counts(normalize=True) * 100
    bezbar_val = counts.get("Так", 0) # Get "Так" or return 0
else:
    bezbar_val = 0

bezbar_str = f"{bezbar_val:,.1f}%"
display_kpi_card(
    "Аналітичні дані", 
    [SumShelter, SumSize, bezbar_str], 
    ["Кількість бомбосховищ", "Загальна місткість", "Рівень інклюзивності"]
)
col1, col2 = st.columns(2)

# --- LEFT COLUMN: PIE CHART ---
with col1:
    type_sum = pd.DataFrame(df_point.groupby("Тип")["Місткість"].sum())
    pie_palette = ["#255c54", "#3d814b", "#8f9e21", "#ffa600"]
    
    pie_chart = px.pie(
        type_sum, 
        names=type_sum.index,
        values="Місткість",
        title="Розподіл місткості за типом",
        color_discrete_sequence=pie_palette,
        hole=0.4
    )
    
    pie_chart.update_layout(
        title_font_size=24,
        legend=dict(font=dict(size=14), orientation="h", y=-0.1), # Move legend to bottom to save width
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    st.plotly_chart(pie_chart, use_container_width=True)

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

    # 3. Plot
    fig_bar = px.bar(
        df_citySize, 
        x=df_citySize.values, 
        y=df_citySize.index, 
        orientation="h", 
        title=title_bar,
        text_auto=True,
        color='Місткість',
        color_continuous_scale=["#53a664", "#255c54"]
    )

    # 4. Styling
    fig_bar.update_layout(
        title_font_size=24,
        xaxis_title=None, # Hide axis title to save space
        yaxis_title=None,
        showlegend=False,
        font=dict(size=14),
        margin=dict(l=20, r=20, t=50, b=20)
    )
    fig_bar.update_traces(textfont_size=16, textposition='outside', cliponaxis=False)

    st.plotly_chart(fig_bar, use_container_width=True)


 