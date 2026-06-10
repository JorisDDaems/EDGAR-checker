"""
monitor.py — entry point.

Orchestreert de scan:
  1. Keyword-scan  — vindt onbekende bedrijven via anchor + sector keywords
  2. Watchlist-scan — vindt 8-Ks van tickers die je al volgt

Draait via: python monitor.py
Automatisch: Windows Task Scheduler -> python C:/edgar_monitor/monitor.py
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime

import config
from deduplicator import Deduplicator
from edgar_client import EdgarClient
from models import Filing, ScanResultaat
from notifier import GmailNotifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Scan-logica
# ---------------------------------------------------------------------------

def keyword_scan(client: EdgarClient, dedup: Deduplicator) -> list[Filing]:
    """
    Zoekt 8-Ks op via precisie-queries uit config.ALLE_QUERIES.
    Elke query is al een gecombineerde AND-expressie (bv. '"IDIQ" "awarded"').
    EDGAR doet full-text matching op de volledige query — geen extra filtering nodig.
    """
    gezien:   set[str]    = set()
    filings:  list[Filing] = []

    for query in config.ALLE_QUERIES:
        hits = client.zoek_op_query(query)
        for hit in hits:
            fid = hit.get("_id", "")
            if not fid or fid in gezien or dedup.is_reeds_gemeld(fid):
                continue
            gezien.add(fid)

            filing = client.parse_keyword_filing(hit, query)
            filings.append(filing)
            logger.info("Keyword hit: %s (%s)", filing.bedrijf, filing.ticker or "geen ticker")

    logger.info("Keyword-scan: %d unieke filing(s)", len(filings))
    return filings


def watchlist_scan(client: EdgarClient, dedup: Deduplicator, keyword_ids: set[str]) -> list[Filing]:
    """
    Zoekt 8-Ks op voor elke watchlist-ticker via exact ticker-field matching.
    Slaat filings over die al door de keyword-scan gevangen zijn.
    """
    gezien:   set[str]    = keyword_ids.copy()   # voorkomt ook overlap met keyword-scan
    filings:  list[Filing] = []

    for ticker in config.WATCHLIST_TICKERS:
        hits = client.zoek_op_ticker(ticker)
        for hit in hits:
            fid = hit.get("_id", "")
            if not fid or fid in gezien or dedup.is_reeds_gemeld(fid):
                continue
            gezien.add(fid)

            if client.is_watchlist_match(hit, ticker):
                filing = client.parse_watchlist_filing(hit, ticker)
                filings.append(filing)
                logger.info("Watchlist hit: %s (%s)", filing.bedrijf, ticker)

    logger.info("Watchlist-scan: %d unieke filing(s)", len(filings))
    return filings


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"\n{'='*60}")
    print(f"EDGAR 8-K Monitor — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"Terugkijkperiode: {config.LOOKBACK_DAGEN} dag(en)")
    print(f"{'='*60}")

    client   = EdgarClient()
    dedup    = Deduplicator()
    notifier = GmailNotifier()

    print("\nKeyword-scan...")
    kw_filings = keyword_scan(client, dedup)

    print("\nWatchlist-scan...")
    kw_ids     = {f.id for f in kw_filings}
    wl_filings = watchlist_scan(client, dedup, kw_ids)

    resultaat = ScanResultaat(
        watchlist_hits = wl_filings,
        keyword_hits   = kw_filings,
    )

    print(f"\n{resultaat.totaal} relevante filing(s) gevonden.")

    if resultaat.heeft_resultaten:
        notifier.verstuur(resultaat)
        alle_ids = [f.id for f in kw_filings + wl_filings]
        dedup.markeer_als_gemeld(alle_ids)
        dedup.opslaan()
    else:
        print("Geen relevante filings vandaag — geen mail verstuurd.")

    print(f"{'='*60}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyError as exc:
        logger.critical(
            "Ontbrekende omgevingsvariabele: %s\n"
            "Controleer je .env bestand (zie README).", exc
        )
        sys.exit(1)
    except Exception as exc:
        logger.critical("Monitor crasht: %s", exc, exc_info=True)
        sys.exit(1)