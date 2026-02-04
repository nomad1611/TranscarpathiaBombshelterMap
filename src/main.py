import pandas as pd
import data_processing as dp
from IPython.display import display


raw_dataset = dp.get_Bombshelter_info()
geo_data= pd.json_normalize(raw_dataset['features'])
display(geo_data)

 