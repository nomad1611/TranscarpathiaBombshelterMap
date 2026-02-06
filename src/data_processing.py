import ckanapi
from ckanapi.errors import NotFound,CKANAPIError, NotAuthorized
from requests_cache  import CachedSession
import config
import pandas as pd

session = CachedSession(
    expire_after = 600
)

def get_Bombshelter_info():
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
    row_data = get_Bombshelter_info()
    df_bombshelter = pd.json_normalize(row_data, record_path=['features'])
    
    coords_df = pd.DataFrame(df_bombshelter['geometry.coordinates'].to_list(), index = df_bombshelter.index)
    
    df_bombshelter['longitude'] = coords_df[0]
    df_bombshelter['latitude'] = coords_df[1]
    return df_bombshelter


    
