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
MAX_GEMELDE_IDS   = 2000   # max te bewaren IDs (FIFO op volgorde van toevoeging)

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
# Keyword-scan — filing moet ≥1 anchor EN ≥1 sector keyword bevatten
# ---------------------------------------------------------------------------
KEYWORDS_ANCHOR = [
    "memorandum of understanding",
    "government contract",
    "strategic investment",
    "equity stake",
    "department of energy",
    "department of defense",
    "awarded contract",
    "binding agreement",
    "offtake agreement",
]

KEYWORDS_SECTOR = [
    "nuclear",          "uranium",          "rare earth",
    "critical minerals","defense",          "drone",
    "unmanned",         "missile",          "navy",
    "air force",        "semiconductor",    "AI infrastructure",
    "sovereign cloud",  "photonics",        "aerospace",
    "hypersonic",       "satellite",        "directed energy",
]

# ---------------------------------------------------------------------------
# Corporate proxy (optioneel)
# Laat leeg als je thuis werkt of geen proxy nodig hebt.
# Voorbeeld: http://10.20.98.14:8080
# ---------------------------------------------------------------------------
CORPORATE_PROXY = os.environ.get("CORPORATE_PROXY", "")