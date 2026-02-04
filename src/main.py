import pandas as pd
import data_processing as dp
from IPython.display import display


raw_dataset = dp.get_Bombshelter_info()
geo_data = dp.get_normalize_data()
display(raw_dataset)
print("*normalize data:*")
display(geo_data.head())

 