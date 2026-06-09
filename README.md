# EDGAR 8-K Monitor

Dagelijkse scan van SEC EDGAR op relevante 8-K filings. Gmail notificatie bij treffer.

## Projectstructuur

```
edgar_monitor/
├── .env.template     ← kopieer naar .env, vul in, nooit in git
├── .env              ← jouw credentials (aanmaken via .env.template)
├── config.py         ← alle configuratie: tickers, keywords, instellingen
├── models.py         ← datastructuren (Filing, ScanResultaat)
├── edgar_client.py   ← EDGAR API communicatie
├── deduplicator.py   ← voorkomt dubbele meldingen
├── notifier.py       ← Gmail HTML-mail
├── monitor.py        ← entry point / orchestratie
└── requirements.txt
```

**Aanpassen doe je enkel in `config.py` en `.env`. De rest hoef je nooit aan te raken.**

---

## Setup (eenmalig, ~10 minuten)

### 1. Python en dependencies

```cmd
pip install -r requirements.txt
```

### 2. Gmail App Password aanmaken

1. Ga naar [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   *(2-stapsverificatie moet actief zijn)*
2. Geef een naam: `EDGAR Monitor`
3. Kopieer het 16-karakter wachtwoord

### 3. .env aanmaken

```cmd
copy .env.template .env
```

Open `.env` in Notepad en vul in:

```
GMAIL_AFZENDER=jouwnaam@gmail.com
GMAIL_APP_PASSWORD=abcd efgh ijkl mnop
GMAIL_ONTVANGER=jouwnaam@gmail.com
```

### 4. Manuele test

```cmd
cd C:\edgar_monitor
python monitor.py
```

Verwachte output:
```
============================================================
EDGAR 8-K Monitor — 09/06/2026 07:00
Terugkijkperiode: 1 dag(en)
============================================================
Keyword-scan...
Watchlist-scan...
X relevante filing(s) gevonden.
============================================================
```

Als je een mail ontvangt: alles werkt.
Als er niets gevonden is: normaal — geen mail verstuurd.

### 5. Windows Task Scheduler

1. `Win+S` → zoek **Taakplanner**
2. Klik rechts → **Eenvoudige taak maken**
3. Naam: `EDGAR 8-K Monitor`
4. Trigger: **Dagelijks** → 07:00
5. Actie: **Een programma starten**
   - Programma: `python` (of volledig pad: `where python` in CMD)
   - Argumenten: `monitor.py`
   - Beginnen in: `C:\edgar_monitor`
6. Klik **Voltooien**

Test: rechts klikken op taak → **Uitvoeren** → check Gmail.

---

## Configuratie aanpassen

Alles staat in `config.py`:

| Wat | Variabele | Voorbeeld |
|-----|-----------|-----------|
| Tickers volgen | `WATCHLIST_TICKERS` | `"BWXT"` toevoegen |
| Anchor keywords | `KEYWORDS_ANCHOR` | `"joint venture"` toevoegen |
| Sector keywords | `KEYWORDS_SECTOR` | `"geothermal"` toevoegen |
| Terugkijkperiode | `LOOKBACK_DAGEN` | `3` voor na een weekend |

---

## Hoe de mail lezen

| Label | Betekenis | Actie |
|-------|-----------|-------|
| ⭐ WATCHLIST | Bedrijf op jouw watchlist heeft een 8-K ingediend | Altijd checken |
| 🔍 KEYWORD | Onbekend bedrijf met anchor + sector match | Open filing, zoek EX-99.1 |

**EX-99.1** = het echte persbericht. Dat is wat je wil lezen.

---

## Troubleshooting

**`SMTPAuthenticationError`**
→ App Password fout of 2FA niet actief.
Check: `myaccount.google.com/apppasswords`

**`KeyError: 'GMAIL_AFZENDER'`**
→ `.env` bestand ontbreekt of variabele niet ingevuld.
Controleer: staat `.env` in dezelfde map als `monitor.py`?

**Geen mail maar geen fout**
→ Vandaag gewoon geen relevante filings. Test met `LOOKBACK_DAGEN = 7` in `config.py`.

**Wil ik controleren wat er gevonden werd zonder mail?**
→ Voeg `logging.basicConfig(level=logging.DEBUG)` toe bovenaan `monitor.py` voor gedetailleerde output.
