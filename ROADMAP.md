# ROADMAP.md

Technische Verbesserungen und Feature-Ideen.

> Diese Liste dient als interne Gedankenstütze.
> Es besteht kein Anspruch auf Umsetzung oder Zeitplan.

---

## Erledigt ✅

- [x] Output-Datei-Validierung nach Pandoc-Konvertierung
- [x] Format-Validierung extrahieren (DRY) → `parse_formats()`
- [x] Encoding-Fallback für Frontmatter-Parser (latin-1)
- [x] Import-Organisation korrigieren (`import re`)
- [x] SUPPORTED_FORMATS Konstante einführen
- [x] Unused Imports entfernen
- [x] Lazy Import in converter_service.py entfernt
- [x] Entry Points für CLI (`mdconv`, `mdconv-ui`)
- [x] Profile erweitert: display_name, description, toc, number_sections

---

## Feature-Ideen

### Logo-Integration in Kopfzeile
- Logo-Bild pro Profil oder global konfigurierbar
- Position: links, mitte, rechts (einstellbar)
- Umsetzung: Pandoc-Variable + Template-Support

### Dokumentenversionierung
- Automatische Versionsnummer aus Frontmatter
- Revision/Status-Feld (Draft, Final, etc.)
- Dokument-ID generieren (z.B. `DOC-2024-001`)

### Erweiterte Profil-Eigenschaften

| Kategorie | Eigenschaften |
|-----------|---------------|
| **Minimal** | Logo, Titel, Untertitel, Version, Datum, Kunde, Projekt, Output-Naming |
| **Erweitert** | Revision, Status, Dokument-ID, TOC pro Profil, Nummerierung |
| **Optional** | Ersteller, Tool/Build-Info, Footer-Hinweis |

### Datenquellen-Trennung

| Quelle | Inhalt |
|--------|--------|
| YAML Frontmatter | Variable Inhalte (Titel, Version, Kunde, Projekt) |
| Profil | Layout & Regeln (Logo, TOC, Naming, Nummerierung) |
| Tool | Defaults & Automatik (Datum, Doc-ID, Build-Info) |
| Template | Darstellung (Position, Schrift, Stil) |

---

## Technische Verbesserungen (offen)

### Mittlere Priorität

- Exception-Handling präzisieren (`except Exception` zu breit)
- Type Hints korrigieren in batch_service.py

### Niedrige Priorität

- Enum für OutputFormat statt Strings
- Thread-Safety für Batch-Service bei paralleler Nutzung
- Chardet-Integration für automatische Encoding-Erkennung
- Validierung von Pandoc-Args in Profilen

---

## Zukünftige Überlegungen

- Config-YAML für benutzerdefinierte Profile
- LaTeX-Template-Support für PDF
- Installer / Packaging (PyInstaller, MSI)
- Mehrsprachige UI
