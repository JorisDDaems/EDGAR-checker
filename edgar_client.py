"""
edgar_client.py — communicatie met de SEC EDGAR full-text search API.

Eén verantwoordelijkheid: HTTP requests naar EDGAR sturen en
de raw JSON omzetten naar Filing objecten. Geen emaillogica hier.
"""

from __future__ import annotations

import json
import logging
import ssl
import urllib.parse
import urllib.request
from datetime import date, timedelta

import certifi
import config
from models import Filing, FilingType

logger = logging.getLogger(__name__)


class EdgarClient:
    """Thin wrapper rond de EDGAR full-text search API."""

    _FORM_TYPE  = "8-K"
    _USER_AGENT = "BAK-monitor jorisddaems@gmail.com"

    # ------------------------------------------------------------------
    # Publieke interface
    # ------------------------------------------------------------------

    def zoek_op_query(self, query: str) -> list[dict]:
        """
        Stuur een query naar EDGAR. De query wordt NIET nogmaals in quotes
        gewikkeld — de caller is verantwoordelijk voor de juiste syntax.
        Voorbeeld: 'memorandum of understanding government'
        """
        return self._fetch(query)

    def zoek_op_ticker(self, ticker: str) -> list[dict]:
        """Geeft ruwe EDGAR hits terug voor één ticker."""
        return self._fetch(ticker)

    # ------------------------------------------------------------------
    # Parsing — van raw hit naar Filing
    # ------------------------------------------------------------------

    @staticmethod
    def parse_keyword_filing(hit: dict, query: str) -> Filing:
        src = hit.get("_source", {})

        # EDGAR display_names formaat: ["SI INTERNATIONAL INC  (CIK 0001143363)"]
        # Ticker zit niet in display_names — aparte 'tickers' field gebruiken
        display_names = src.get("display_names", [])
        bedrijf = display_names[0].split("(CIK")[0].strip() if display_names else "Onbekend"
        tickers = src.get("tickers", [])
        ticker  = tickers[0].upper() if tickers else ""

        return Filing(
            id          = hit.get("_id", ""),
            bedrijf     = bedrijf,
            ticker      = ticker,
            periode     = src.get("period_of_report", src.get("period_ending", "")),
            filing_type = FilingType.KEYWORD,
            match_info  = f"Query: {query}",
        )

    @staticmethod
    def parse_watchlist_filing(hit: dict, ticker: str) -> Filing:
        src = hit.get("_source", {})
        display_names = src.get("display_names", [])
        bedrijf = display_names[0].split("(CIK")[0].strip() if display_names else "Onbekend"

        return Filing(
            id          = hit.get("_id", ""),
            bedrijf     = bedrijf,
            ticker      = ticker.upper(),
            periode     = src.get("period_of_report", src.get("file_date", "")),
            filing_type = FilingType.WATCHLIST,
            match_info  = f"Watchlist ticker: {ticker}",
        )

    @staticmethod
    def is_watchlist_match(hit: dict, ticker: str) -> bool:
        """
        Exact ticker matching via display_names[].ticker field.
        Geen substring matching op bedrijfsnaam — dat geeft false positives.
        """
        src     = hit.get("_source", {})
        tickers = [t.upper() for t in src.get("tickers", [])]
        return ticker.upper() in tickers

    # ------------------------------------------------------------------
    # Interne HTTP helpers
    # ------------------------------------------------------------------

    def _fetch(self, query: str) -> list[dict]:
        vandaag    = date.today()
        startdatum = (vandaag - timedelta(days=config.LOOKBACK_DAGEN)).isoformat()

        # filed_at wordt genegeerd door dit EDGAR endpoint — datumfilter
        # gebeurt daarom in Python na het ophalen via file_date in _source.
        params = {
            "q":     query,
            "forms": self._FORM_TYPE,
            "from":  0,
            "size":  config.MAX_RESULTATEN,
        }
        url = f"{config.EDGAR_BASE_URL}?{urllib.parse.urlencode(params)}"
        logger.debug("GET %s", url)

        opener = self._build_opener()
        req = urllib.request.Request(url, headers={"User-Agent": self._USER_AGENT})
        try:
            with opener.open(req, timeout=config.REQUEST_TIMEOUT) as resp:
                data = json.loads(resp.read().decode())
                hits = data.get("hits", {}).get("hits", [])
                return [h for h in hits if self._binnen_lookback(h, startdatum)]
        except urllib.error.HTTPError as exc:
            logger.error("EDGAR HTTP %s voor query '%s'", exc.code, query)
            return []
        except urllib.error.URLError as exc:
            logger.error("EDGAR verbindingsfout voor query '%s': %s", query, exc.reason)
            return []
        except json.JSONDecodeError as exc:
            logger.error("EDGAR ongeldig JSON antwoord voor query '%s': %s", query, exc)
            return []

    @staticmethod
    def _binnen_lookback(hit: dict, startdatum: str) -> bool:
        """Behoud alleen filings waarvan file_date >= startdatum."""
        file_date = hit.get("_source", {}).get("file_date", "")
        if not file_date:
            return False
        return file_date >= startdatum

    @staticmethod
    def _build_opener() -> urllib.request.OpenerDirector:
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        https_handler = urllib.request.HTTPSHandler(context=ssl_ctx)
        return urllib.request.build_opener(https_handler)