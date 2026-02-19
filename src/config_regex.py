import re

# ---------------------------------------------------------------------------
# Pre-compiled regular expressions
# (compiled once at module load time instead of on every function call)
# ---------------------------------------------------------------------------
_RE_WHITESPACE = re.compile(r"\s+")
_RE_TRAILING_LETTER = re.compile(r"\s+[А-Яа-яA-Za-z]\b$")
_RE_DIGITS_QUOTES = re.compile(r'[\d",]')
_RE_EDGE_DOT = re.compile(r"\.$|^\.")
_RE_NEWLINE_TAB = re.compile(r"[\n\t]")
_RE_DASH_SPACES = re.compile(r"\s*-\s*")
_RE_NON_DIGIT = re.compile(r"[А-Яа-яA-Za-z]")
_RE_EXTRA_QUOTES = re.compile(r'[""„?»«]')
_RE_OTG_SUFFIX = re.compile(r"\s+(?:ТГ|ОТГ|тг|отг|СТГ|стг).*$", re.IGNORECASE)
_RE_CITY_STREET_SFX = re.compile(
    r"(?:\s+(?:вул\.|ул\.|пл\.|кв\.).*|вул)\s*$", re.IGNORECASE
)
_RE_CITY_PREFIX = re.compile(
    r"^\s*(?:м\.|с\.|смт\.?|пос\.|місто|село|селище)\s*", re.IGNORECASE
)
_RE_EDGE_DOT_SPACE = re.compile(r"^[.\s]+")
_RE_ADDR_NEWLINE = re.compile(r"[\n\t]")
_RE_ADDR_EDGE_DOT = re.compile(r"\.$|^\.")
_RE_ADDR_NUMBER_ONLY = re.compile(r"^(?:№\s?)?\d+(?:[.\-]?\d+|[\s-]?[а-яА-Яa-zA-Z])?$")
_RE_ADDR_CITY_PREFIX = re.compile(r"(?i).+?\b(вул(?:иця)?\s*[.,]?\s*.*)$")
_RE_ADDR_SPLIT_LN = re.compile(r"([а-яА-Яa-zA-Z])(\d)")
_RE_ADDR_SPLIT_NL = re.compile(r"(\d)([а-яА-Яa-zA-Z])")
_RE_ADDR_VUL = re.compile(r"(?i)\b(вул|ул)\b[.,]?\s*")
_RE_ADDR_PL = re.compile(r"(?i)\b(пл\.|площа)\s*")
_RE_ADDR_PR = re.compile(r"(?i)\b(пр\.|проспект|просп\.)\s*")
_RE_ADDR_BUD = re.compile(r"(?i)\b(буд|ьуд)\s*\.?\s*(?![а-яА-Яa-zA-ZіїєґІЇЄҐ])")
_RE_ADDR_BUDYNOK = re.compile(r"(?i)\b(будинок|будівля)\b")
_RE_ADDR_DUP_VUL = re.compile(r"(вул\.\s*)+")
_RE_NAME_EDGE = re.compile(r"^[.,\s]+|[.,\s]+$")
