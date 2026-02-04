import pandas as pd
import data_processing as dp
import IPython.display as display


raw_dataset = dp.get_Bombshelter_info()
geo_data= pd.json_normalize(raw_dataset['features'])
print(geo_data)

 