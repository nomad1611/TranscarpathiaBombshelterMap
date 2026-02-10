import ckanapi
from ckanapi.errors import NotFound,CKANAPIError, NotAuthorized
from requests_cache  import CachedSession
import config
import pandas as pd

session = CachedSession(
    expire_after = 600
)

def get_raw_api_info():
    try:
        ua_portal = ckanapi.RemoteCKAN(config.URL_CARP_GOV_UA)
        metadata = ua_portal.action.package_show(id=config.ID_BOMBSHELTER)
        

        recources_url = None
        for resources in metadata['resources']:
            if resources['format'].lower() == 'geojson':
                resources_url = resources['url']
                break
        if resources_url:
            response = session.get(resources_url)
            response.raise_for_status()
            source: str = 'CACHE' if getattr(response, 'from_cache', False) else 'API'
            print(source)
            return  response.json()  
            

    except NotFound:
         print("Error: ID of dataset doesn`t exist on this site;")
    except NotAuthorized:
        print("Error: This dataset is private or requires API key to access;")
    except CKANAPIError as e:
        print(f"Error:A CKAN API error occured: {e}; ")
    except Exception as e:
        print(f"An unexpected error ocurred: {e};")
    
    return None


def get_normalize_data():
    row_data = get_raw_api_info()
    df_bombshelter = pd.json_normalize(row_data, record_path=['features'])
    
    coords_df = pd.DataFrame(df_bombshelter['geometry.coordinates'].to_list(), index = df_bombshelter.index)
    
    df_bombshelter['longitude'] = coords_df[0]
    df_bombshelter['latitude'] = coords_df[1]
    return df_bombshelter

def get_city_info(cityName:str, df:pd.DataFrame)-> pd.DataFrame:
        df_categorized = df[(df["properties.City"] == cityName)]
        return df_categorized 

def get_cityName(df:pd.DataFrame) -> pd.Series:
    df_cityName = df["properties.City"].drop_duplicates().squeeze().sort_values()
    df
    return df_cityName

def clean_data_info(df:pd.DataFrame) -> pd.DataFrame :
    
    
    return df

def clean_str(s:pd.Series) -> pd.Series:
    
    s_str = s.copy().astype(dtype=str)

    homoglyphs = {
    'A': 'А', 'B': 'В', 'C': 'С', 'E': 'Е', 'H': 'Н', 'I': 'І', 'K': 'К', 
    'M': 'М', 'O': 'О', 'P': 'Р', 'T': 'Т', 'X': 'Х', 'i': 'і', 'y': 'у',
    'a': 'а', 'c': 'с', 'e': 'е', 'o': 'о', 'p': 'р', 'x': 'х'
    }
    trans_table = str.maketrans(homoglyphs)
    s = s.apply(lambda x: x.translate(trans_table))
    
    s_str = s_str.str.replace(r'[\n\t]', '', regex=True)
    s_str = s_str.str.replace('`',"'").str.replace("’", "'")
    s_str = s_str.str.replace(r'\s*-\s*', '-', regex=True) 
    s_str = s_str.str.replace(r'\s+[А-Яа-яA-za-z]\b$', '', regex=True) 
    s_str = s_str.str.replace(r'[\d\",]', '', regex=True) 
    s_str = s_str.str.replace(r'\.$|^\.', '', regex=True)
    s_str = s_str.str.strip()
    
    return s_str


