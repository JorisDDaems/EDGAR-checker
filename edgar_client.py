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

    _FORM_TYPE   = "8-K"
    _USER_AGENT  = "BAK-monitor jorisddaems@gmail.com"

    # ------------------------------------------------------------------
    # Publieke interface
    # ------------------------------------------------------------------

    def zoek_op_keyword(self, keyword: str) -> list[dict]:
        """Geeft ruwe EDGAR hits terug voor één keyword."""
        return self._fetch(f'"{keyword}"')

    def zoek_op_ticker(self, ticker: str) -> list[dict]:
        """
        Geeft ruwe EDGAR hits terug voor één ticker.
        Zoekt op de exacte ticker string — EDGAR indexeert deze in het
        volledige document, inclusief het tickers[] field.
        """
        return self._fetch(ticker)

    # ------------------------------------------------------------------
    # Parsing — van raw hit naar Filing
    # ------------------------------------------------------------------

    @staticmethod
    def parse_keyword_filing(hit: dict, keyword: str) -> Filing:
        src    = hit.get("_source", {})
        ticker = EdgarClient._extract_ticker(src)
        tekst  = json.dumps(hit).lower()
        sector_matches = [k for k in config.KEYWORDS_SECTOR if k.lower() in tekst]

        return Filing(
            id          = hit.get("_id", ""),
            bedrijf     = src.get("entity_name", "Onbekend"),
            ticker      = ticker,
            periode     = src.get("period_of_report", ""),
            filing_type = FilingType.KEYWORD,
            match_info  = (
                f"Anchor: {keyword} | "
                f"Sector: {', '.join(sector_matches[:4]) or '—'}"
            ),
        )

    @staticmethod
    def parse_watchlist_filing(hit: dict, ticker: str) -> Filing:
        src = hit.get("_source", {})
        return Filing(
            id          = hit.get("_id", ""),
            bedrijf     = src.get("entity_name", "Onbekend"),
            ticker      = ticker,
            periode     = src.get("period_of_report", ""),
            filing_type = FilingType.WATCHLIST,
            match_info  = f"Watchlist ticker: {ticker}",
        )

    @staticmethod
    def is_watchlist_match(hit: dict, ticker: str) -> bool:
        src     = hit.get("_source", {})
        tickers = [t.upper() for t in src.get("tickers", [])]
        return ticker.upper() in tickers

    @staticmethod
    def is_keyword_relevant(hit: dict) -> bool:
        tekst = json.dumps(hit).lower()
        heeft_anchor = any(kw.lower() in tekst for kw in config.KEYWORDS_ANCHOR)
        heeft_sector  = any(kw.lower() in tekst for kw in config.KEYWORDS_SECTOR)
        return heeft_anchor and heeft_sector

    # ------------------------------------------------------------------
    # Interne HTTP helpers
    # ------------------------------------------------------------------

    def _fetch(self, query: str) -> list[dict]:
        vandaag    = date.today()
        startdatum = (vandaag - timedelta(days=config.LOOKBACK_DAGEN)).isoformat()
        einddatum  = vandaag.isoformat()

        # filed_at=start,end is de correcte datumfilter voor dit endpoint.
        # dateRange=custom&startdt=...&enddt=... geeft altijd 0 resultaten.
        params = {
            "q":       query,
            "forms":   self._FORM_TYPE,
            "filed_at": f"{startdatum},{einddatum}",
            "from":    0,
            "size":    config.MAX_RESULTATEN,
        }
        url = f"{config.EDGAR_BASE_URL}?{urllib.parse.urlencode(params)}"
        logger.debug("GET %s", url)

        opener = self._build_opener()
        req = urllib.request.Request(url, headers={"User-Agent": self._USER_AGENT})
        try:
            with opener.open(req, timeout=config.REQUEST_TIMEOUT) as resp:
                data = json.loads(resp.read().decode())
                return data.get("hits", {}).get("hits", [])
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
    def _build_opener() -> urllib.request.OpenerDirector:
        """
        Gebruik de Windows certificate store (via python-certifi-win32) zodat
        het corporate proxy-certificaat vertrouwd wordt zonder SSL te bypassen.
        """
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        https_handler = urllib.request.HTTPSHandler(context=ssl_ctx)
        return urllib.request.build_opener(https_handler)

    @staticmethod
    def _extract_ticker(src: dict) -> str:
        tickers = src.get("tickers", [])
        return tickers[0].upper() if tickers else ""