import pandas as pd
import plotly.express as px
import streamlit as st



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
    


def display_pie_chart(df_sum: pd.DataFrame, color_palette:dict|None, value:str = None, title: str|None=None ):
    pie_chart = px.pie(
        df_sum, 
        names=df_sum.index,
        values=value,
        title=title,
        color_discrete_sequence=color_palette,
        hole=0.4
    )
    
    pie_chart.update_layout(
        title_font_size=24,
        legend=dict(font=dict(size=18), orientation="h", y=-0.1), # Move legend to bottom to save width
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    st.plotly_chart(pie_chart, width="stretch")

def display_bar_chart(s: pd.Series, title: str|None=None, color: str|None = None, color_palette:dict |None = None):
    fig_bar = px.bar(
        s, 
        x=s.values, 
        y=s.index, 
        orientation="h", 
        title=title,
        text_auto=True,
        color=color,
        color_continuous_scale=color_palette
    )

    # 4. Styling
    fig_bar.update_layout(
        title_font_size=24,
        xaxis_title=None, # Hide axis title to save space
        yaxis_title=None,
        showlegend=False,
        font=dict(size=18),
        margin=dict(l=20, r=20, t=50, b=20)
    )
    fig_bar.update_traces(textfont_size=16, textposition='outside', cliponaxis=False)

    st.plotly_chart(fig_bar, width="stretch")
