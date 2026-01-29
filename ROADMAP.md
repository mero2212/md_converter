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
- [x] Lokale Daten von Git getrennt (`local/`, `local_profiles.py`)

---

## Lokale Daten (nicht auf GitHub)

Firmenspezifische Daten bleiben lokal und werden nicht veröffentlicht:

```
local/                    # Gitignored
├── templates/            # DOCX Templates mit Logo
├── logos/                # Firmenlogos
└── README.md             # Anleitung

local_profiles.py              # Eigene Profile (gitignored)
local_profiles.py.example      # Vorlage (im Repo)
create_templates.py            # Template-Generator mit Firmenadresse (gitignored)
create_templates.py.example    # Vorlage (im Repo)
templates/                     # Platzhalter für Templates
```

### Was bleibt lokal?

| Lokal (privat) | GitHub (öffentlich) |
|----------------|---------------------|
| Firmenlogo | Code & Logik |
| Corporate Templates | Standard-Profile |
| Kundennamen | Beispieldateien |
| Versionsnummern | Dokumentation |
| Eigene Profile | Tests |

---

## Feature-Ideen

### Mermaid-Diagramm-Support 🎯 (In Arbeit)

Mermaid-Codeblöcke in Markdown automatisch zu Bildern konvertieren.

**Warum Mermaid?**
- Textbasiert → Git-freundlich
- Sehr weit verbreitet (GitHub, GitLab, Obsidian, VS Code, Notion)
- Flowcharts, Sequenzdiagramme, ER-Diagramme, Gantt, etc.

**Technische Umsetzung:**

```
Markdown mit Mermaid → Pre-Processing → Markdown mit Bildern → Pandoc → DOCX/PDF
```

| Schritt | Beschreibung |
|---------|--------------|
| 1. Scan | Markdown nach ```mermaid Codeblöcken durchsuchen |
| 2. Render | Mit `mmdc` (Mermaid CLI) zu PNG rendern |
| 3. Replace | Codeblock durch `![](temp/diagram.png)` ersetzen |
| 4. Convert | Pandoc wie gewohnt ausführen |
| 5. Cleanup | Temporäre Bilder löschen |

**Ausgabeformat:**
- PNG für DOCX (Word mag kein SVG)
- PNG für PDF (zuverlässiger als SVG in LaTeX)

**Voraussetzung:**
```bash
npm install -g @mermaid-js/mermaid-cli
```

**Dateien:**
- `converter/mermaid_processor.py` - Mermaid-Verarbeitung
- Integration in `converter_service.py`

---

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
