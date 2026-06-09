"""
models.py — datastructuren voor de applicatie.

Geen plain dicts. Elke typo in een veldnaam is nu een AttributeError
bij het schrijven van de code, niet een silent bug bij runtime.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class FilingType(Enum):
    WATCHLIST = "WATCHLIST"
    KEYWORD   = "KEYWORD"


@dataclass(frozen=True)
class Filing:
    """Eén EDGAR 8-K filing, volledig geparsed."""
    id:          str          # EDGAR _id, gebruikt voor deduplicatie en directe link
    bedrijf:     str
    ticker:      str          # uit EDGAR tickers[] field, leeg string als afwezig
    periode:     str          # period_of_report
    filing_type: FilingType
    match_info:  str          # human-readable reden waarom dit een match is

    @property
    def edgar_url(self) -> str:
        """
        Directe link naar de filing op EDGAR.
        _id heeft de vorm '/Archives/edgar/data/CIK/ACNR/filing-index.htm'
        """
        if self.id.startswith("/"):
            return f"https://www.sec.gov{self.id}"
        return f"https://efts.sec.gov/LATEST/search-index?q=%22{self.id}%22&forms=8-K"


@dataclass(frozen=True)
class ScanResultaat:
    """Alle bevindingen van één monitor-run, gegroepeerd per type."""
    watchlist_hits: list[Filing]
    keyword_hits:   list[Filing]

    @property
    def heeft_resultaten(self) -> bool:
        return bool(self.watchlist_hits or self.keyword_hits)

    @property
    def totaal(self) -> int:
        return len(self.watchlist_hits) + len(self.keyword_hits)
