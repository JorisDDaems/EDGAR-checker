"""
config.py — alle configuratie op één plek.

Credentials komen uit .env (nooit in git zetten).
Keywords en watchlist mag je hier gewoon bewerken.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# ---------------------------------------------------------------------------
# Gmail — stel in via .env bestand (zie README)
# ---------------------------------------------------------------------------
GMAIL_AFZENDER     = os.environ["GMAIL_AFZENDER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
GMAIL_ONTVANGER    = os.environ["GMAIL_ONTVANGER"]

# ---------------------------------------------------------------------------
# EDGAR API
# ---------------------------------------------------------------------------
EDGAR_BASE_URL  = "https://efts.sec.gov/LATEST/search-index"
LOOKBACK_DAGEN  = 7      # dagen terug om te scannen (1 = afgelopen 24u)
REQUEST_TIMEOUT = 15     # seconden per HTTP request
MAX_RESULTATEN  = 40     # EDGAR max per query

# ---------------------------------------------------------------------------
# Bestand voor deduplicatie — voorkomt dubbele meldingen
# ---------------------------------------------------------------------------
REEDS_GEMELD_FILE = Path(__file__).parent / "edgar_reeds_gemeld.json"
MAX_GEMELDE_IDS   = 2000

# ---------------------------------------------------------------------------
# Watchlist — altijd melden bij een 8-K, ongeacht keywords
# ---------------------------------------------------------------------------
WATCHLIST_TICKERS = [
    "BWXT", "LEU",  "AVAV", "LHX",  "AMTM", "MP",
    "VST",  "NOW",  "APH",  "AMBA", "INFQ", "KTOS",
    "RBBN", "WCC",  "NXPI", "CRDO", "PDYN", "HYLN",
    "UEC",  "CVU",  "CLF",  "SCWO", "HON",  "XYL",  "VPK",
]

# ---------------------------------------------------------------------------
# Keyword queries — aanhalingstekens voor exact-phrase matching
#
# EDGAR interpreteert "phrase one" "phrase two" als:
# beide exacte zinnen moeten aanwezig zijn in de filing.
#
# Groep A — hoge precisie, bijna altijd een echte deal
# ---------------------------------------------------------------------------
QUERIES_HOGE_PRECISIE = [
    '"awarded" "department of defense"',
    '"awarded" "department of energy"',
    '"entered into a definitive agreement"',
    '"memorandum of understanding" "department of defense"',
    '"memorandum of understanding" "department of energy"',
    '"memorandum of understanding" "government"',
    '"selected as" "prime contractor"',
    '"strategic investment" "equity" "defense"',
    '"strategic investment" "equity" "nuclear"',
    '"letter of intent" "defense"',
    '"letter of intent" "nuclear"',
    '"IDIQ" "awarded"',
    '"sole source" "contract"',
    '"offtake agreement" "uranium"',
    '"offtake agreement" "rare earth"',
]

# ---------------------------------------------------------------------------
# Groep B — medium precisie
# ---------------------------------------------------------------------------
QUERIES_MEDIUM_PRECISIE = [
    '"government contract" "nuclear"',
    '"government contract" "uranium"',
    '"government contract" "rare earth"',
    '"government contract" "drone"',
    '"government contract" "unmanned"',
    '"government contract" "semiconductor"',
    '"government contract" "hypersonic"',
    '"government contract" "directed energy"',
    '"awarded contract" "navy"',
    '"awarded contract" "air force"',
    '"equity stake" "nuclear"',
    '"equity stake" "defense"',
    '"equity stake" "semiconductor"',
    '"strategic partnership" "rare earth"',
    '"strategic partnership" "critical minerals"',
]

# ---------------------------------------------------------------------------
# Gecombineerde lijst — monitor.py gebruikt deze ene variabele
# ---------------------------------------------------------------------------
ALLE_QUERIES = QUERIES_HOGE_PRECISIE + QUERIES_MEDIUM_PRECISIE

# ---------------------------------------------------------------------------
# Corporate proxy (optioneel)
# ---------------------------------------------------------------------------
CORPORATE_PROXY = os.environ.get("CORPORATE_PROXY", "")