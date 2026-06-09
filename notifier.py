"""
notifier.py — Gmail notificatie.

Eén verantwoordelijkheid: een ScanResultaat omzetten naar een HTML-mail
en versturen. Weet niets van EDGAR of scan-logica.
"""

from __future__ import annotations

import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config
from models import Filing, FilingType, ScanResultaat

logger = logging.getLogger(__name__)

_SMTP_HOST = "smtp.gmail.com"
_SMTP_PORT = 465

_KLEUR = {
    FilingType.WATCHLIST: "#e65c00",
    FilingType.KEYWORD:   "#1565C0",
}
_LABEL = {
    FilingType.WATCHLIST: "⭐ WATCHLIST",
    FilingType.KEYWORD:   "🔍 KEYWORD",
}


class GmailNotifier:
    """Verstuurt een HTML-mail voor een ScanResultaat."""

    def verstuur(self, resultaat: ScanResultaat) -> None:
        if not resultaat.heeft_resultaten:
            logger.info("Geen relevante filings — geen mail verstuurd.")
            return

        msg = self._bouw_bericht(resultaat)
        self._verstuur_smtp(msg)

    # ------------------------------------------------------------------
    # Bericht opbouw
    # ------------------------------------------------------------------

    def _bouw_bericht(self, resultaat: ScanResultaat) -> MIMEMultipart:
        datum     = datetime.now().strftime("%d/%m/%Y")
        onderwerp = f"🔭 EDGAR 8-K Alert — {resultaat.totaal} filing(s) — {datum}"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = onderwerp
        msg["From"]    = config.GMAIL_AFZENDER
        msg["To"]      = config.GMAIL_ONTVANGER
        msg.attach(MIMEText(self._render_html(resultaat), "html"))
        return msg

    def _render_html(self, resultaat: ScanResultaat) -> str:
        # Watchlist altijd eerst — dat zijn de bekende namen
        alle_filings = resultaat.watchlist_hits + resultaat.keyword_hits
        rijen = "\n".join(self._render_rij(f) for f in alle_filings)
        timestamp = datetime.now().strftime("%d %B %Y om %H:%M")

        return f"""
<html><body style="font-family:Arial,sans-serif;max-width:820px;margin:0 auto;color:#333;">

  <div style="background:#0d1b2a;color:white;padding:20px 25px;border-radius:8px 8px 0 0;">
    <h2 style="margin:0;font-size:20px;">🔭 SEC EDGAR 8-K Monitor</h2>
    <p style="margin:6px 0 0;opacity:0.75;font-size:13px;">
      {resultaat.totaal} nieuwe relevante filing(s) gedetecteerd — {timestamp}
    </p>
  </div>

  <div style="background:#fff8e1;padding:12px 20px;border-left:4px solid #f9a825;font-size:13px;">
    <strong>Volgende stap:</strong> open de filing → zoek bijlage <strong>EX-99.1</strong>
    (= het echte persbericht) → stuur ticker naar Claude met <em>"check dit"</em>
    voor volledige drie-criteria analyse.
  </div>

  <table style="width:100%;border-collapse:collapse;font-size:13px;">
    <thead>
      <tr style="background:#f0f4f8;">
        <th style="padding:10px 12px;text-align:left;width:30%;">Bedrijf</th>
        <th style="padding:10px 12px;text-align:left;width:45%;">Match-reden</th>
        <th style="padding:10px 12px;text-align:left;width:25%;">Link</th>
      </tr>
    </thead>
    <tbody>{rijen}</tbody>
  </table>

  <div style="background:#f5f5f5;padding:14px 20px;border-radius:0 0 8px 8px;
              font-size:11px;color:#888;margin-top:0;">
    Drie-criteria reminder: trigger ✓ | anchor-validator ✓ | koers ≤150% van 52w laag ✓<br>
    Script draait dagelijks via Windows Task Scheduler. Duplicaten worden automatisch gefilterd.
  </div>

</body></html>"""

    @staticmethod
    def _render_rij(filing: Filing) -> str:
        kleur = _KLEUR[filing.filing_type]
        label = _LABEL[filing.filing_type]
        return f"""
        <tr>
          <td style="padding:12px;border-bottom:1px solid #eee;vertical-align:top;">
            <span style="background:{kleur};color:white;padding:2px 8px;
                  border-radius:3px;font-size:11px;font-weight:bold;">{label}</span><br><br>
            <strong style="font-size:14px;">{filing.bedrijf}</strong>
            {f'<em style="color:#555;font-size:12px;"> ({filing.ticker})</em>' if filing.ticker else ''}
            <br><span style="color:#888;font-size:12px;">Periode: {filing.periode or '—'}</span>
          </td>
          <td style="padding:12px;border-bottom:1px solid #eee;vertical-align:top;font-size:13px;">
            {filing.match_info}
          </td>
          <td style="padding:12px;border-bottom:1px solid #eee;vertical-align:top;">
            <a href="{filing.edgar_url}" style="color:#1565C0;font-size:13px;">📄 Open op EDGAR</a>
          </td>
        </tr>"""

    # ------------------------------------------------------------------
    # SMTP
    # ------------------------------------------------------------------

    def _verstuur_smtp(self, msg: MIMEMultipart) -> None:
        # Poort 587 + STARTTLS — wordt zelden geblokkeerd door corporate proxy.
        # Poort 465 (SMTP_SSL) wordt vaak geblokkeerd.
        try:
            with smtplib.SMTP(_SMTP_HOST, 587) as server:
                server.ehlo()
                server.starttls()
                server.login(config.GMAIL_AFZENDER, config.GMAIL_APP_PASSWORD)
                server.sendmail(
                    config.GMAIL_AFZENDER,
                    config.GMAIL_ONTVANGER,
                    msg.as_string(),
                )
            logger.info("Mail verstuurd naar %s", config.GMAIL_ONTVANGER)
        except smtplib.SMTPAuthenticationError:
            logger.error(
                "Authenticatiefout — check App Password via "
                "myaccount.google.com/apppasswords"
            )
            raise
        except smtplib.SMTPException as exc:
            logger.error("Gmail SMTP fout: %s", exc)
            raise