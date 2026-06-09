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
LOOKBACK_DAGEN  = 1      # dagen terug om te scannen (1 = afgelopen 24u)
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
# Keyword-scan — hoge precisie
#
# Elke query wordt apart naar EDGAR gestuurd.
# Een filing telt mee als de volledige query matcht — EDGAR doet full-text
# search op de combinatie, dus je kan AND-logica inbouwen met spaties.
#
# Groep A — bijna altijd een echte deal, weinig ruis
# ---------------------------------------------------------------------------
QUERIES_HOGE_PRECISIE = [
    '"awarded a contract" "department of"',
    '"entered into a definitive agreement"',
    '"memorandum of understanding" "department of"',
    '"memorandum of understanding" "government"',
    '"selected as" "prime contractor"',
    '"selected as" "contractor"',
    '"strategic investment" "equity"',
    '"strategic investment" "stake"',
    '"letter of intent" "defense"',
    '"letter of intent" "nuclear"',
    '"letter of intent" "energy"',
    '"letter of intent" "semiconductor"',
    '"IDIQ" "awarded"',        # Indefinite Delivery — sterkste contractvorm
    '"IDIQ" "selected"',
    '"sole source" "awarded"', # Geen concurrentie = bijzonder sterk signaal
    '"sole source" "contract"',
    '"offtake agreement"',
    '"binding agreement" "government"',
]

# ---------------------------------------------------------------------------
# Groep B — medium precisie, altijd gecombineerd met sector
# ---------------------------------------------------------------------------
QUERIES_MEDIUM_PRECISIE = [
    '"government contract" "nuclear"',
    '"government contract" "uranium"',
    '"government contract" "rare earth"',
    '"government contract" "drone"',
    '"government contract" "unmanned"',
    '"government contract" "autonomous"',
    '"government contract" "semiconductor"',
    '"government contract" "photonics"',
    '"government contract" "AI infrastructure"',
    '"government contract" "hypersonic"',
    '"government contract" "directed energy"',
    '"government contract" "satellite"',
    '"awarded contract" "department of defense"',
    '"awarded contract" "department of energy"',
    '"equity stake" "nuclear"',
    '"equity stake" "defense"',
    '"equity stake" "semiconductor"',
    '"equity stake" "rare earth"',
]

# ---------------------------------------------------------------------------
# Gecombineerde lijst — monitor.py gebruikt deze ene variabele
# ---------------------------------------------------------------------------
ALLE_QUERIES = QUERIES_HOGE_PRECISIE + QUERIES_MEDIUM_PRECISIE

# ---------------------------------------------------------------------------
# Corporate proxy (optioneel)
# ---------------------------------------------------------------------------
CORPORATE_PROXY = os.environ.get("CORPORATE_PROXY", "")