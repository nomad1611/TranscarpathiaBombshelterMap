import ckanapi
import requests
from ckanapi.errors import NotFound,CKANAPIError, NotAuthorized
from requests_cache  import CachedSession
import streamlit as st
import config
import pandas as pd
import re

session = CachedSession(
    expire_after = 600
)
@st.cache_data
def __get_raw_api_info():
    try:
        ua_portal = ckanapi.RemoteCKAN(config.URL_CARP_GOV_UA)
        metadata = ua_portal.action.package_show(id=config.ID_BOMBSHELTER)
        

        recources_url = None
        for resources in metadata['resources']:
            if resources['format'].lower() == 'geojson':
                resources_url = resources['url']
                break
        if resources_url:
            response = requests.get(resources_url)
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

@st.cache_data
def get_normalize_data():
    row_data = __get_raw_api_info()
    df_bombshelter = pd.json_normalize(row_data, record_path = ['features'])
    df_bombshelter = df_bombshelter.drop(columns=['type','geometry.type', 'properties.Number'], errors="ignore")
    df_bombshelter = __clean_data_info(df=df_bombshelter)
    return df_bombshelter


@st.cache_data
def get_extended_data(df_bombshelter:pd.DataFrame) -> pd.DataFrame:
    df = df_bombshelter.copy()
    df = __get_googlemaps_links(df)
    df['properties.Bezbar'] = df['properties.Bezbar'].map({True:'Так', False:'Ні'}).fillna('Невідомо')
    df = df.rename(columns={
    'properties.Name': 'Назва',
    'properties.OTG': 'ОТГ',
    'properties.City': 'Населений пункт',
    'properties.Rajon':'Район',
    'properties.Area' : 'Площа',
    'properties.Property':'Власність',
    'properties.Adress': 'Адреса',
    'properties.Type': 'Тип',
    'properties.TypeZs': 'Будова',
    'properties.People': 'Місткість',
    'properties.Bezbar': 'Інклюзивність',
    'link': "Посилання"
})
    
    
    return df


def get_city_info(OTGName:str, df:pd.DataFrame)-> pd.Series:
        
    if OTGName == " ":
           df_categorized = df["properties.City"]
    
    else:
        df_categorized = df[(df["properties.OTG"] == OTGName)]["properties.City"]
        
    sorted_cities = get_sorted_columnData(df_categorized)
    return [" "] + sorted_cities 

@st.cache_data
def get_sorted_columnData(s:pd.Series) -> pd.Series:
    
    s_sorted =s.dropna().unique().tolist()
    s_sorted = sorted(s_sorted, key=__ukr_sort_key)

    return s_sorted


def search_data(
    df: pd.DataFrame, 
    cityName: str | None = None, 
    OTG: str | None = None, 
    Type: list[str] | None = None, 
    Size: int | None = None, 
    Bezbar: bool | None = None
) -> pd.DataFrame:
    
    mask = pd.Series(True, index=df.index)

    if cityName != " ":
        mask &= (df['Населений пункт'] == cityName)
        
    if OTG != " ":
        mask &= (df['ОТГ'] == OTG)

    if Type and len(Type) > 0:
        mask &= (df['Тип'].isin(Type))
    
    if Bezbar: 
        
        mask &= (df['Інклюзивність'] == 'Так')
   
    if Size:
       
        mask &= (df['Місткість'] <= Size)

    return df[mask]



def __ukr_sort_key(text):
    ukr_alphabet = "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ"
    sort_map = {c: i for i, c in enumerate(ukr_alphabet)}
    return [sort_map.get(c.upper(), 999) for c in text]



def __get_googlemaps_links(df:pd.DataFrame) -> pd.DataFrame:
    lat = df['latitude'].astype(str)
    lng= df['longitude'].astype(str)

    df['link']='https://www.google.com/maps?q='+lat+","+lng

    return df



def __clean_data_info(df:pd.DataFrame) -> pd.DataFrame :
    df_clean = (
        df.copy()
        .assign(**{
              "properties.OTG" : lambda x: __clean_properties_OTG(x["properties.OTG"]),
              "properties.City" : lambda x: __clean_properties_City(x["properties.City"]),
               "properties.Name": lambda x: __clean_properties_Name(x["properties.Name"]),
               "properties.Area": lambda x: __clean_num(x["properties.Area"]),
               "properties.People": lambda x: __clean_num(x["properties.People"]),
               'properties.TypeZs': lambda x: __clean_str_strict(x['properties.TypeZs']),
               'properties.Type': lambda x: __clean_str_strict(x['properties.Type']),
               'properties.Rajon': lambda x: __clean_str_strict(x['properties.Rajon']),
               'properties.Bezbar': lambda x: __clean_bool(x['properties.Bezbar']),
               'properties.Adress': lambda x: __clean_properties_Adress(x['properties.Adress'])
               })
               .pipe(__merge_geometry_columns))
    df_clean = df_clean.drop(columns=['geometry.coordinates'], errors='ignore')
    
    return df_clean



def __merge_geometry_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Calculate coords
    coords = __normalize_geometry_coordinates(df['geometry.coordinates'])
    # Add them to the dataframe
    df['longitude'] = coords['longitude']
    df['latitude'] = coords['latitude']
    return df



def __clean_str_base(s:pd.Series) -> pd.Series:
    s_str = s.astype(dtype=str)
    homoglyphs = {
    'A': 'А', 'B': 'В', 'C': 'С', 'E': 'Е', 'H': 'Н', 'I': 'І', 'K': 'К', 
    'M': 'М', 'O': 'О', 'P': 'Р', 'T': 'Т', 'X': 'Х', 'i': 'і', 'y': 'у',
    'a': 'а', 'c': 'с', 'e': 'е', 'o': 'о', 'p': 'р', 'x': 'х'}

    trans_table = str.maketrans(homoglyphs)
    s_str = s_str.apply(lambda x: x.translate(trans_table))
    
    s_str = s_str.str.replace('`',"'").str.replace("’", "'")
    s_str = s_str.str.replace(r'\s*-\s*', '-', regex=True) 
    
    return s_str.str.strip()



def __clean_str_strict(s:pd.Series) -> pd.Series:
    s_str = __clean_str_base(s.astype(dtype=str))

    s_str = s_str.str.replace(r'[\n\t]', '', regex=True)
    s_str = s_str.str.replace(r'\s+[А-Яа-яA-za-z]\b$', '', regex=True) 
    s_str = s_str.str.replace(r'[\d\",]', '', regex=True) 
    s_str = s_str.str.replace(r'\.$|^\.', '', regex=True)
    
    return s_str.str.strip()



def __clean_num(s:pd.Series) -> pd.Series:
    
    t = s.dtype
    if t == int or t == float or t == complex:
        return s

    s_Num = s.astype(dtype=str)
    s_Num = s_Num.str.replace(r'\s+', '', regex=True)
    s_Num = s_Num.str.replace(r'[А-Яа-яA-za-z]', '', regex=True) 
    
    regexQuotes = r'[“”„\?»«]'
    s_Num = s_Num.str.replace(regexQuotes, '', regex=True)

    s_Num = s_Num.str.replace(',' , '.') 
    
    s_Num = s_Num.str.strip()

    return pd.to_numeric(s_Num)



def __clean_bool(s:pd.Series) -> pd.Series:
    
    s_bezbar = s.astype(str).str.lower().str.strip()

    bool_map = {'true': True, 'false': False}
    s_bezbar = s_bezbar.replace(bool_map)
    s_bezbar.loc[s_bezbar.isna()] = False
    
    return s_bezbar.astype(bool)



def __clean_properties_OTG(s: pd.Series) -> pd.Series:
    
    s_otg = __clean_str_strict(s)

    combined_regex = r'(?:\s+(?:ТГ|ОТГ|тг|отг|СТГ|стг).*$)' 
    s_otg = s_otg.str.replace(combined_regex, '', regex=True, flags=re.IGNORECASE)
    
    fixed_dctionary = {
    'Усть-Чорна':'Усть-Чорнянська',
    'Косонська' : 'Косоньська',
    }
    s_otg = s_otg.replace(fixed_dctionary)

    return s_otg.str.strip()



def __clean_properties_City(s : pd.Series) -> pd.Series:
    
    s_city = __clean_str_strict(s)

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



def __clean_properties_Name(s: pd.Series) -> pd.Series:

    s_Name = __clean_str_base(s)

    s_Name = s_Name.str.replace(r'\s+', ' ', regex=True)
    s_Name = s_Name.str.replace(r'^[.,\s]+|[.,\s]+$', '', regex=True)
    
    regexQuotes = r'[“”„\?»«]'
    s_Name = s_Name.str.replace(regexQuotes, '"', regex=True)

    


    s_Name = s_Name.str.slice(0, 1).str.upper() + s_Name.str.slice(1)
    

    
    return s_Name.str.strip()



def __clean_properties_Adress(s: pd.Series) -> pd.Series:
    s_adress = s.astype(str)
    
    
    s_adress = s_adress.str.replace(r'[\n\t]', ' ', regex=True)
    s_adress = s_adress.str.replace(r'\s+', ' ', regex=True)
    s_adress = s_adress.str.replace(r'\.$|^\.', '', regex=True)
    
    
    regexQuotes = r'[“”„\?»«]'
    s_adress = s_adress.str.replace(regexQuotes, '"', regex=True)
    
    
    regexNumber = r'^(?:№\s?)?\d+(?:[.\-]?\d+|[\s-]?[а-яА-Яa-zA-Z])?$'
    s_adress = s_adress.str.replace(regexNumber, "Відсутня", regex=True)
    
    
    regexCity = r'(?i).+?\b(вул(?:иця)?\s*[.,]?\s*.*)$'
    s_adress = s_adress.str.replace(regexCity, r'\1', regex=True)
    
    
    # Розділяємо "ЛітериЦифри" (Виноградна17 -> Виноградна 17)
    s_adress = s_adress.str.replace(r'([а-яА-Яa-zA-Z])(\d)', r'\1\, \2', regex=True)
    
    s_adress = s_adress.str.replace(r'(\d)([а-яА-Яa-zA-Z])', r'\1 \2', regex=True)

    
    exact_dict = {
        'Миру': 'вул. Миру',
        'Шевченка': 'вул. Шевченка',
        'Студентська набережна': 'наб. Студентська',
        'без назви': 'вул. Без Назви', 
        'Без назви': 'вул. Без Назви',
        'наб. Киівська, 16': 'наб. Київська, 16',
        'вул.Пушкіна (Й. Волощукв), 2' : 'вул. Пушкіна (Й. Волощука), 2',
        'с.Руська Мокра, Тячівського району, Миру, 97':'вул. Миру, 97',
        'вул. Визволення, 21 /2-пов будівля/': 'вул. Визволення, 21',
        'вул. Європейська, 18 Тячівського району' : 'вул. Європейська, 18'
    }
    s_adress = s_adress.replace(exact_dict)

    # Виправляємо "вул."
    # \b на початку і в кінці гарантує, що це окреме слово
    s_adress = s_adress.str.replace(r'(?i)\b(вул|ул)\b[.,]?\s*', 'вул. ', regex=True)
    
    s_adress = s_adress.str.replace(r'(?i)\b(пл\.|площа)\s*', 'пл. ', regex=True)
    
    s_adress = s_adress.str.replace(r'(?i)\b(пр\.|проспект|просп\.)\s*', 'пр. ', regex=True)
    
    # (?!\w) означає "наступний символ НЕ буква". 
    s_adress = s_adress.str.replace(r'(?i)\b(буд|ьуд)\s*\.?\s*(?![а-яА-Яa-zA-ZіїєґІЇЄҐ])', 'буд. ', regex=True)
    

    s_adress = s_adress.str.replace(r'(?i)\b(будинок|будівля)\b', 'буд.', regex=True)

    s_adress = s_adress.str.replace(r'(вул\.\s*)+', 'вул. ', regex=True)

    return s_adress.str.strip()



def __normalize_geometry_coordinates(s: pd.Series) -> pd.DataFrame:
    coords_df = pd.DataFrame(s.to_list(), index = s.index)

    coords_df[0] = __clean_num(coords_df[0])
    coords_df[1] = __clean_num(coords_df[1])
    
    coords_df = coords_df.rename(columns={ 0:'longitude', 1:'latitude'})
    
    return coords_df



