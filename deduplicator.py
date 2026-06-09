"""
deduplicator.py — voorkomt dat dezelfde filing twee keer gemeld wordt.

Bewaart een lijst van reeds gemelde filing-IDs in een JSON bestand.
FIFO-queue: als het bestand te groot wordt, vallen de oudste IDs eraf.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import config

logger = logging.getLogger(__name__)


class Deduplicator:
    """
    Beheert een persistente set van reeds gerapporteerde filing-IDs.

    Gebruik:
        ded = Deduplicator()
        if not ded.is_reeds_gemeld(fid):
            # verwerk filing
            ...
        ded.markeer_als_gemeld([fid1, fid2])
        ded.opslaan()
    """

    def __init__(self, pad: Path = config.REEDS_GEMELD_FILE) -> None:
        self._pad      = pad
        self._gemeld   = self._laad()      # ordered list, nieuwste achteraan
        self._gemeld_set = set(self._gemeld)  # O(1) lookups

    # ------------------------------------------------------------------
    # Publieke interface
    # ------------------------------------------------------------------

    def is_reeds_gemeld(self, filing_id: str) -> bool:
        return filing_id in self._gemeld_set

    def markeer_als_gemeld(self, filing_ids: list[str]) -> None:
        for fid in filing_ids:
            if fid not in self._gemeld_set:
                self._gemeld.append(fid)
                self._gemeld_set.add(fid)

    def opslaan(self) -> None:
        """Bewaar naar schijf. Knip af op MAX_GEMELDE_IDS (FIFO — oudste eraf)."""
        te_bewaren = self._gemeld[-config.MAX_GEMELDE_IDS:]
        try:
            self._pad.write_text(json.dumps(te_bewaren), encoding="utf-8")
            logger.debug("%d filing-IDs opgeslagen in %s", len(te_bewaren), self._pad)
        except OSError as exc:
            logger.error("Kon %s niet schrijven: %s", self._pad, exc)

    # ------------------------------------------------------------------
    # Intern
    # ------------------------------------------------------------------

    def _laad(self) -> list[str]:
        try:
            data = json.loads(self._pad.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
            logger.warning("%s bevat geen lijst — reset naar leeg", self._pad)
            return []
        except FileNotFoundError:
            return []
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Kon %s niet lezen (%s) — start met lege set", self._pad, exc)
            return []
