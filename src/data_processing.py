import ckanapi
from ckanapi.errors import NotFound,CKANAPIError, NotAuthorized
from requests_cache  import CachedSession
import config
import pandas as pd
import re

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



def clean_str_base(s:pd.Series) -> pd.Series:
    s_str = s.astype(dtype=str)
    homoglyphs = {
    'A': 'А', 'B': 'В', 'C': 'С', 'E': 'Е', 'H': 'Н', 'I': 'І', 'K': 'К', 
    'M': 'М', 'O': 'О', 'P': 'Р', 'T': 'Т', 'X': 'Х', 'i': 'і', 'y': 'у',
    'a': 'а', 'c': 'с', 'e': 'е', 'o': 'о', 'p': 'р', 'x': 'х'
    }
    trans_table = str.maketrans(homoglyphs)
    s_str = s_str.apply(lambda x: x.translate(trans_table))
    
    s_str = s_str.str.replace('`',"'").str.replace("’", "'")
    s_str = s_str.str.replace(r'\s*-\s*', '-', regex=True) 
    
    return s_str.str.strip()



def clean_str_strict(s:pd.Series) -> pd.Series:
    s_str = clean_str_base(s.astype(dtype=str))

    s_str = s_str.str.replace(r'[\n\t]', '', regex=True)
    s_str = s_str.str.replace(r'\s+[А-Яа-яA-za-z]\b$', '', regex=True) 
    s_str = s_str.str.replace(r'[\d\",]', '', regex=True) 
    s_str = s_str.str.replace(r'\.$|^\.', '', regex=True)
    
    return s_str.str.strip()

def clean_num(s:pd.Series) -> pd.Series:
    s_Num = s.astype(dtype=str)
    s_Num = s_Num.str.replace(r'\s+', '', regex=True)
    s_Num = s_Num.str.replace(r'[А-Яа-яA-za-z]', '', regex=True) 
    
    regexQuotes = r'[“”„\?»«]'
    s_Num = s_Num.str.replace(regexQuotes, '', regex=True)

    s_Num = s_Num.str.replace(',' , '.') 
    
    s_Num = s_Num.str.strip()

    return pd.to_numeric(s_Num)


def clean_bool(s:pd.Series) -> pd.Series:
    
    s_bezbar = clean_str_strict(s)

    s_bezbar = s_bezbar.str.lower()

    bool_map = {'true': True, 'false': False}
    s_bezbar = s_bezbar.replace(bool_map)
    s_bezbar.loc[s_bezbar.isna()] = False
    
    return s_bezbar.astype(bool)

def clean_properties_OTG(s: pd.Series) -> pd.Series:
    
    s_otg = clean_str_strict(s)

    combined_regex = r'(?:\s+(?:ТГ|ОТГ|тг|отг|СТГ|стг).*$)' 
    s_otg = s_otg.str.replace(combined_regex, '', regex=True, flags=re.IGNORECASE)
    
    fixed_dctionary = {
    'Усть-Чорна':'Усть-Чорнянська',
    'Косонська' : 'Косоньська',
    }
    s_otg = s_otg.replace(fixed_dctionary)

    return s_otg.str.strip()



def clean_properties_City(s : pd.Series) -> pd.Series:
    
    s_city = clean_str_strict(s)

    combined_regex = r'(?:\s+(?:вул\.|ул\.|пл\.|кв\.).*|вул)\s*$'
    s_city = s_city.str.replace(combined_regex, '', regex=True, flags=re.IGNORECASE)
    
    prefix_pattern = r'^\s*(?:м\.|с\.|смт\.?|пос\.|місто|село|селище)\s*'
    s_city = s_city.str.replace(prefix_pattern, "", regex=True, flags=re.IGNORECASE)

    s_city = s_city.str.replace(r'^[.\s]+', '', regex=True)
    
    abbreviation_map = {
            'Вел. Бичків': 'Великий Бичків',
            'В.Бичків': 'Великий Бичків',
            'В.Ворота': 'Верхні Ворота',
            'В. Ворота': 'Верхні Ворота',
            'Н.Ворота': 'Нижні Ворота',
            'В.Коропець': 'Верхній Коропець',
            'Н.Коропець': 'Нижній Коропець',
            'В.Визниця': 'Верхня Визниця',
            'М.Раковець': 'Малий Раковець',
            'В.Раковець': 'Великий Раковець',
            'Р.Поле': 'Руське Поле',
            'Н.Селище': 'Нижнє Селище',
            'В.Водяне': 'Верхнє Водяне',
            'Н.Давидково':'Нове Давидково', 
            'Н. Ремета' : 'Нижні Ремети',
            }
    s_city = s_city.replace(abbreviation_map)
    
    typo_correct = {
        'Золотарево': 'Золотарьово',
        'Зарічово': 'Зарічево',
        'Копашнево': 'Копашново',
        'Кленовець': 'Кленовець',
        'Клиновець': 'Кленовець',
        'Верхне Водяне': 'Верхнє Водяне',
        'Горінчево': 'Горінчово',
        'Усть- Чорна': 'Усть-Чорна',
        'Бедевля': 'Бедевля',
        'Березово':'Березове',
        'Оклі' : 'Оклі Гедь',
        'Горинчево': 'Горінчово',
        'Вільхівські -Лази':'Вільхівські-Лази',
        'Оклі Гедь Гедь' : 'Оклі Гедь',
        'Неветленфолувул' : 'Неветленфолу'
        }
    s_city = s_city.replace(typo_correct, regex=True)

    return s_city.str.strip()



def clean_properties_Name(s: pd.Series) -> pd.Series:

    s_Name = clean_str_base(s)

    s_Name = s_Name.str.replace(r'\s+', ' ', regex=True)
    s_Name = s_Name.str.replace(r'^[.,\s]+|[.,\s]+$', '', regex=True)
    
    regexQuotes = r'[“”„\?»«]'
    s_Name = s_Name.str.replace(regexQuotes, '"', regex=True)

    


    s_Name = s_Name.str.slice(0, 1).str.upper() + s_Name.str.slice(1)
    

    
    return s_Name.str.strip()


