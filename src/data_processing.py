import logging
import os

import requests
import ckanapi
from ckanapi.errors import NotFound, CKANAPIError, NotAuthorized


import streamlit as st
import pandas as pd

import config_regex as rx
import config

from functools import cmp_to_key

_HOMOGLYPHS: dict[str, str] = {
    "A": "А",
    "B": "В",
    "C": "С",
    "E": "Е",
    "H": "Н",
    "I": "І",
    "K": "К",
    "M": "М",
    "O": "О",
    "P": "Р",
    "T": "Т",
    "X": "Х",
    "i": "і",
    "y": "у",
    "a": "а",
    "c": "с",
    "e": "е",
    "o": "о",
    "p": "р",
    "x": "х",
}
_HOMOGLYPH_TABLE = str.maketrans(_HOMOGLYPHS)

# Ukrainian alphabet order for sorting
_UKR_ALPHABET = "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ"
_UKR_SORT_MAP: dict[str, int] = {c: i for i, c in enumerate(_UKR_ALPHABET)}


@st.cache_resource
def _setup_logger():
    """
    Sets up a logger using st.cache_resource to prevent duplicate
    log handlers when Streamlit reruns the script.
    """

    logger = logging.getLogger("CKAN_App")

    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        log_file_path = "./logs/log.txt"
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


logger = _setup_logger()


@st.cache_data(ttl=3600 * 24)  # 24hrs
def _get_raw_api_info() -> dict | None:
    """Fetch raw GeoJSON data from the carpathia.gov.ua.
    Returns:
        Pased GeoJSON dictionary on success or ``None`` if request fails.
    Raises:
        DataFetchError: Propagated to the caller after displaying an
            ``st.error`` notification so the Streamlit UI can react.

    """
    logger.info(f"Initiating API request to {config.URL_CARP_GOV_UA}")
    logger.debug(f"Parameters: {config.ID_BOMBSHELTER}")

    try:

        ua_portal = ckanapi.RemoteCKAN(config.URL_CARP_GOV_UA)
        metadata = ua_portal.action.package_show(id=config.ID_BOMBSHELTER)

        resources_url: str | None = None
        for resource in metadata["resources"]:
            if resource["format"].lower() == "geojson":
                resources_url = resource["url"]
                logger.info(f"Successfully fetched {resources_url} url from CKAN.")
                break

        if resources_url is None:
            logger.error("GEOJSON resource not found in the dataset metadata.")
            return None

        response = requests.get(resources_url)
        response.raise_for_status()

        source: str = "CACHE" if getattr(response, "from_cache", False) else "API"
        logger.info(f"Successfully fetched data records from {source}.")
        return response.json()

    except NotFound:
        logger.error(
            f"Dataset ID '{config.ID_BOMBSHELTER}' was not found on the portal."
        )
    except NotAuthorized:
        logger.error(
            "Access denied: This dataset is private or requires API key to access;"
        )
    except CKANAPIError as e:
        logger.error(f"Error:A CKAN API error occured: {e}; ")
    except requests.RequestException as exc:
        logger.error(f"Network error while fetching GeoJSON: {exc}")
    except Exception as e:
        logger.error(f"An unexpected error ocurred: {e};")

    return None


@st.cache_data
def get_normalized_data():
    """
    Fetch, clean and normalize data from _get_raw_api_info()
    Returns:
        Cleaned DataFrame or ``None`` if data could not be retrieved
    """
    raw_data = _get_raw_api_info()
    if raw_data is None:
        return None

    df = pd.json_normalize(raw_data, record_path=["features"])
    df = df.drop(
        columns=["type", "geometry.type", "properties.Number"], errors="ignore"
    )
    df = _clean_data_info(df)
    return df


@st.cache_data
def get_extended_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add derived columns and rename to Ukrainian display names.

    Args:
        df: Cleaned DataFrame returned by ``get_normalized_data``.

    Returns:
        Display-ready DataFrame with Ukrainian column headers and a
        Google Maps hyperlink column.
    """
    df = df.copy()
    df = _add_get_googlemaps_links(df)
    df["properties.Bezbar"] = (
        df["properties.Bezbar"].map({True: "Так", False: "Ні"}).fillna("Невідомо")
    )

    column_map: dict[str, str] = {
        "properties.Name": "Назва",
        "properties.OTG": "ОТГ",
        "properties.City": "Населений пункт",
        "properties.Rajon": "Район",
        "properties.Area": "Площа",
        "properties.Property": "Власність",
        "properties.Adress": "Адреса",
        "properties.Type": "Тип",
        "properties.TypeZs": "Будова",
        "properties.People": "Місткість",
        "properties.Bezbar": "Інклюзивність",
        "link": "Посилання",
    }

    return df.rename(columns=column_map)


def get_city_options(otg_name: str, df: pd.DataFrame) -> pd.Series:
    """Return sorted, unique city names, optionally filtered by OTG.

    Args:
        otg_name: OTG (community) name to filter on.  Pass ``" "`` to
            return cities from all communities.
        df: Cleaned DataFrame (before renaming columns).

    Returns:
        List starting with ``" "`` (blank sentinel) followed by unique
        city names sorted by Ukrainian alphabet order.
    """
    city_series = (
        df["properties.City"]
        if otg_name == " "
        else df.loc[df["properties.OTG"] == otg_name, "properties.City"]
    )
    return [" "] + get_sorted_column_values(city_series)


@st.cache_data
def get_sorted_column_values(s: pd.Series) -> pd.Series:
    """Return unique, non-null values from *s* sorted by Ukrainian alphabet.

    Args:
        s: A pandas Series of Ukrainian strings.

    Returns:
        Sorted list of unique string values.
    """
    unique_values = s.dropna().unique().tolist()
    return sorted(unique_values, key=_UKR_KEY)


def search_data(
    df: pd.DataFrame,
    city_name: str | None = None,
    otg_name: str | None = None,
    shelter_type: list[str] | None = None,
    max_capacity: int | None = None,
    accessible_only: bool | None = None,
) -> pd.DataFrame:
    """Filter the display DataFrame by the given criteria.

    Args:
        df: Display-ready DataFrame (Ukrainian column names from
            ``get_extended_data``).
        city_name: Settlement to filter on; ``" "`` means no filter.
        otg: OTG community name; ``" "`` means no filter.
        shelter_type: List of shelter-type strings to include.
        max_capacity: Upper bound on the ``Місткість`` column.
        accessible_only: If ``True``, keep only wheelchair-accessible
            shelters (``Інклюзивність == 'Так'``).

    Returns:
        Filtered DataFrame.
    """

    mask = pd.Series(True, index=df.index)

    if city_name != " ":
        mask &= df["Населений пункт"] == city_name

    if otg_name != " ":
        mask &= df["ОТГ"] == otg_name

    if shelter_type and len(shelter_type) > 0:
        mask &= df["Тип"].isin(shelter_type)

    if accessible_only:

        mask &= df["Інклюзивність"] == "Так"

    if max_capacity:

        mask &= df["Місткість"] <= max_capacity

    return df[mask]


def _ukr_sort_key(text: str) -> list[int]:
    """Return a sort key list based on Ukrainian alphabet order.

    Args:
        text: A Ukrainian (or mixed) string to sort.

    Returns:
        A list of integer positions in the Ukrainian alphabet.
        Unknown characters map to 999 so they sort last.
    """
    return [_UKR_SORT_MAP.get(c.upper(), 999) for c in text]


def _ukr_cmp(a: str, b: str) -> int:
    """Comparator for Ukrainian strings, used with ``cmp_to_key``."""
    ka, kb = _ukr_sort_key(a), _ukr_sort_key(b)
    return (ka > kb) - (ka < kb)


_UKR_KEY = cmp_to_key(_ukr_cmp)


def _add_get_googlemaps_links(df: pd.DataFrame) -> pd.DataFrame:
    """Append a ``link`` column with Google Maps URLs derived from coordinates.

    Args:
        df: DataFrame containing ``latitude`` and ``longitude`` columns.

    Returns:
        DataFrame with an additional ``link`` column.

    Bug fix:
        Original code referenced ``df['latitude']`` / ``df['longitude']``
        but the source columns were named inconsistently in some branches.
        We now rely on the standardised column names set by
        ``_normalize_coordinates``.
    """
    df = df.copy()
    df["link"] = (
        "https://www.google.com/maps?q="
        + df["latitude"].astype(str)
        + ","
        + df["longitude"].astype(str)
    )
    return df


def _clean_data_info(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all column-level cleaning transforms to the raw GeoJSON DataFrame.

    Args:
        df: Raw DataFrame produced by ``pd.json_normalize``.

    Returns:
        Cleaned DataFrame with parsed coordinates.
    """
    df_clean = (
        df.copy()
        .assign(
            **{
                "properties.OTG": lambda x: _clean_otg(x["properties.OTG"]),
                "properties.City": lambda x: _clean_city(x["properties.City"]),
                "properties.Name": lambda x: _clean_name(x["properties.Name"]),
                "properties.Area": lambda x: _clean_num(x["properties.Area"]),
                "properties.People": lambda x: _clean_num(x["properties.People"]),
                "properties.TypeZs": lambda x: _clean_str_strict(
                    x["properties.TypeZs"]
                ),
                "properties.Type": lambda x: _clean_str_strict(x["properties.Type"]),
                "properties.Rajon": lambda x: _clean_str_strict(x["properties.Rajon"]),
                "properties.Bezbar": lambda x: _clean_bool(x["properties.Bezbar"]),
                "properties.Adress": lambda x: _clean_adress(x["properties.Adress"]),
            }
        )
        .pipe(__merge_geometry_columns)
    )
    df_clean = df_clean.drop(columns=["geometry.coordinates"], errors="ignore")

    return df_clean


def __merge_geometry_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Calculate coords
    coords = _normalize_coordinates(df["geometry.coordinates"])
    # Add them to the dataframe
    df["longitude"] = coords["longitude"]
    df["latitude"] = coords["latitude"]
    return df


def _clean_str_base(s: pd.Series) -> pd.Series:
    """Apply base string normalisation: homoglyphs, quotes, dash spacing.

    Args:
        s: Raw string Series.

    Returns:
        Cleaned string Series.
    """
    s_str = s.astype(dtype=str)
    s_str = s.str.translate(_HOMOGLYPH_TABLE)

    s_str = s_str.str.replace("`", "'", regex=False).str.replace(
        "\u2019", "'", regex=False
    )
    s_str = rx._RE_DASH_SPACES.sub("-", s.str.cat(sep="\x00"))

    s_str = s.str.replace(rx._RE_DASH_SPACES, "-", regex=True)
    return s_str.str.strip()


def _clean_str_strict(s: pd.Series) -> pd.Series:
    """Strict string cleaning: removes newlines, stray digits, trailing letters.

    Args:
        s: Raw string Series.

    Returns:
        Cleaned string Series.
    """
    s_str = _clean_str_base(s.astype(dtype=str))

    s_str = s_str.str.replace(rx._RE_NEWLINE_TAB, "", regex=True)
    s_str = s_str.str.replace(rx._RE_TRAILING_LETTER, "", regex=True)
    s_str = s_str.str.replace(rx._RE_DIGITS_QUOTES, "", regex=True)
    s_str = s_str.str.replace(rx._RE_EDGE_DOT, "", regex=True)

    return s_str.str.strip()


def _clean_num(s: pd.Series) -> pd.Series:
    """Coerce a mixed-type Series to numeric, removing units and formatting.

    Args:
        s: Series that may contain numbers stored as strings.

    Returns:
        Numeric (float) Series.

    """

    if s.dtype in (int, float, complex):
        return s

    s = s.astype(dtype=str)
    s = s.str.replace(rx._RE_NON_DIGIT, "", regex=True)
    s = s.str.replace(rx._RE_EXTRA_QUOTES, "", regex=True)
    s = s.str.replace(",", ".", regex=False)

    s = s.str.strip()
    return pd.to_numeric(s)


def _clean_bool(s: pd.Series) -> pd.Series:

    s_bezbar = s.astype(str).str.lower().str.strip()

    bool_map = {"true": True, "false": False}
    s_bezbar = s_bezbar.replace(bool_map)
    s_bezbar.loc[s_bezbar.isna()] = False

    return s_bezbar.astype(bool)


def _clean_otg(s: pd.Series) -> pd.Series:
    """Normalise OTG (community) names.

    Args:
        s: Raw OTG name Series.

    Returns:
        Normalised OTG name Series.
    """
    s = _clean_str_strict(s)
    s = s.str.replace(rx._RE_OTG_SUFFIX, "", regex=True)

    corrections: dict[str, str] = {
        "Усть-Чорна": "Усть-Чорнянська",
        "Косонська": "Косоньська",
    }
    return s.replace(corrections).str.strip()


def _clean_city(s: pd.Series) -> pd.Series:
    """Normalise settlement (city/village) names.

    Args:
        s: Raw city name Series.

    Returns:
        Normalised city name Series.
    """
    s = _clean_str_strict(s)
    s = s.str.replace(rx._RE_CITY_STREET_SFX, "", regex=True)
    s = s.str.replace(rx._RE_CITY_PREFIX, "", regex=True)
    s = s.str.replace(rx._RE_EDGE_DOT_SPACE, "", regex=True)

    abbreviation_map = {
        "Вел. Бичків": "Великий Бичків",
        "В.Бичків": "Великий Бичків",
        "В.Ворота": "Верхні Ворота",
        "В. Ворота": "Верхні Ворота",
        "Н.Ворота": "Нижні Ворота",
        "В.Коропець": "Верхній Коропець",
        "Н.Коропець": "Нижній Коропець",
        "В.Визниця": "Верхня Визниця",
        "М.Раковець": "Малий Раковець",
        "В.Раковець": "Великий Раковець",
        "Р.Поле": "Руське Поле",
        "Н.Селище": "Нижнє Селище",
        "В.Водяне": "Верхнє Водяне",
        "Н.Давидково": "Нове Давидково",
        "Н. Ремета": "Нижні Ремети",
    }
    s = s.replace(abbreviation_map)

    typo_correct = {
        "Золотарево": "Золотарьово",
        "Зарічово": "Зарічево",
        "Копашнево": "Копашново",
        "Кленовець": "Кленовець",
        "Клиновець": "Кленовець",
        "Верхне Водяне": "Верхнє Водяне",
        "Горінчево": "Горінчово",
        "Усть- Чорна": "Усть-Чорна",
        "Бедевля": "Бедевля",
        "Березово": "Березове",
        "Оклі": "Оклі Гедь",
        "Горинчево": "Горінчово",
        "Вільхівські -Лази": "Вільхівські-Лази",
        "Оклі Гедь Гедь": "Оклі Гедь",
        "Неветленфолувул": "Неветленфолу",
    }

    return s.replace(typo_correct).str.strip()


def _clean_name(s: pd.Series) -> pd.Series:
    """Normalise shelter name: collapse whitespace, fix quotes, capitalise.

    Args:
        s: Raw name Series.

    Returns:
        Normalised name Series.
    """
    s = _clean_str_base(s)
    s = s.str.replace(rx._RE_WHITESPACE, " ", regex=True)
    s = s.str.replace(rx._RE_NAME_EDGE, "", regex=True)
    s = s.str.replace(rx._RE_EXTRA_QUOTES, '"', regex=True)
    # Capitalise first character using vectorised string operations
    s = s.str[:1].str.upper() + s.str[1:]
    return s.str.strip()


def _clean_adress(s: pd.Series) -> pd.Series:
    """Normalise Ukrainian postal address strings.

    Args:
        s: Raw address Series.

    Returns:
        Normalised address Series.
    """
    s_adress = s.astype(str)
    s_adress = s_adress.str.replace(rx._RE_ADDR_NEWLINE, " ", regex=True)
    s_adress = s_adress.str.replace(rx._RE_WHITESPACE, " ", regex=True)
    s_adress = s_adress.str.replace(rx._RE_ADDR_EDGE_DOT, "", regex=True)
    s_adress = s_adress.str.replace(rx._RE_EXTRA_QUOTES, '"', regex=True)
    s_adress = s_adress.str.replace(rx._RE_ADDR_NUMBER_ONLY, "Відсутня", regex=True)
    s_adress = s_adress.str.replace(rx._RE_ADDR_CITY_PREFIX, r"\1", regex=True)
    s_adress = s_adress.str.replace(rx._RE_ADDR_SPLIT_LN, r"\1, \2", regex=True)
    s_adress = s_adress.str.replace(rx._RE_ADDR_SPLIT_NL, r"\1 \2", regex=True)

    exact_dict: dict[str, str] = {
        "Миру": "вул. Миру",
        "Шевченка": "вул. Шевченка",
        "Студентська набережна": "наб. Студентська",
        "без назви": "вул. Без Назви",
        "Без назви": "вул. Без Назви",
        "наб. Киівська, 16": "наб. Київська, 16",
        "вул.Пушкіна (Й. Волощукв), 2": "вул. Пушкіна (Й. Волощука), 2",
        "с.Руська Мокра, Тячівського району, Миру, 97": "вул. Миру, 97",
        "вул. Визволення, 21 /2-пов будівля/": "вул. Визволення, 21",
        "вул. Європейська, 18 Тячівського району": "вул. Європейська, 18",
    }
    s_adress = s_adress.replace(exact_dict)

    s_adress = s_adress.str.replace(rx._RE_ADDR_VUL, "вул. ", regex=True)
    s_adress = s_adress.str.replace(rx._RE_ADDR_PL, "пл. ", regex=True)
    s_adress = s_adress.str.replace(rx._RE_ADDR_PR, "пр. ", regex=True)
    s_adress = s_adress.str.replace(rx._RE_ADDR_BUD, "буд. ", regex=True)
    s_adress = s_adress.str.replace(rx._RE_ADDR_BUDYNOK, "буд.", regex=True)
    s_adress = s_adress.str.replace(rx._RE_ADDR_DUP_VUL, "вул. ", regex=True)
    return s.str.strip()


def _normalize_coordinates(s: pd.Series) -> pd.DataFrame:
    """Expand a Series of [lon, lat] lists into a two-column DataFrame.

    Args:
        s: Series whose values are two-element coordinate lists.

    Returns:
        DataFrame with columns ``longitude`` and ``latitude``.
    """
    coords_df = pd.DataFrame(s.to_list(), index=s.index)

    coords_df[0] = _clean_num(coords_df[0])
    coords_df[1] = _clean_num(coords_df[1])

    coords_df = coords_df.rename(columns={0: "longitude", 1: "latitude"})

    return coords_df
