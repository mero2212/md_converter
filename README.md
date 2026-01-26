# Markdown to DOCX Converter

> **Status**
>
> This is a personal utility project.
>
> - Public for transparency and reference
> - Local / offline usage only
> - No support, no issue tracking, no feature requests
> - Provided as-is, without warranty

Ein lokales Konvertierungstool, das Markdown-Dateien (.md) zuverlässig in Word-Dokumente (.docx) umwandelt.

## Features

- ✅ Konvertierung von Markdown zu Word (.docx) **und PDF**
- ✅ Unterstützung für technische Dokumente (Überschriften, Listen, Tabellen)
- ✅ **YAML Frontmatter** für Metadaten (Titel, Autor, Version, Datum, etc.)
- ✅ **Preset-Profile** (angebot, report, schulung) mit konfigurierbaren Defaults
- ✅ **Referenz-DOCX-Templates** für Corporate-Layout
- ✅ **Batch-Konvertierung** (Ordner → Ordner, rekursiv)
- ✅ **Mehrfach-Format-Export** (z.B. docx + pdf in einem Durchgang)
- ✅ Optional: Verwendung von Word-Templates für konsistente Formatierung
- ✅ Saubere Fehlermeldungen
- ✅ Logging auf INFO/ERROR-Level
- ✅ Plattformunabhängig (primär für Windows entwickelt)
- ✅ **Unit-Tests** mit pytest

## Voraussetzungen

### Python

- Python 3.7 oder höher

### Pandoc

Das Tool verwendet **Pandoc** als Konvertierungs-Engine. Pandoc muss separat installiert werden:

1. **Windows**: 
   - Download: https://github.com/jgm/pandoc/releases/latest
   - Installer herunterladen und ausführen
   - Oder via Chocolatey: `choco install pandoc`

2. **Alternative Installation**:
   - Offizielle Website: https://pandoc.org/installing.html

3. **Verifizierung**:
   ```bash
   pandoc --version
   ```

### LaTeX (für PDF-Export)

Für PDF-Export wird eine **LaTeX-Distribution** benötigt:

1. **Windows**: 
   - **MiKTeX**: https://miktex.org/download
   - **TeX Live**: https://www.tug.org/texlive/windows.html
   - Empfohlen: MiKTeX (einfachere Installation)

2. **Linux**:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install texlive-xetex texlive-luatex texlive-latex-base
   
   # Oder nur eine Engine:
   sudo apt-get install texlive-xetex  # für xelatex
   ```

3. **macOS**:
   - **MacTeX**: https://www.tug.org/mactex/
   - Oder via Homebrew: `brew install --cask mactex`

4. **Verifizierung**:
   ```bash
   xelatex --version  # oder lualatex, pdflatex
   ```

**Hinweis**: Das Tool sucht automatisch nach verfügbaren PDF-Engines (xelatex, lualatex, pdflatex) in dieser Reihenfolge.

## Installation

1. Repository klonen oder herunterladen
2. (Optional) Virtuelle Umgebung erstellen:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. Python-Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```

## UX starten (Streamlit)

Für eine lokale Drag&Drop-UX kann die Streamlit-App gestartet werden:

```bash
pip install -r requirements.txt
streamlit run ui_app.py
```

**Hinweis**: Pandoc muss installiert sein. Für PDF-Export zusätzlich LaTeX (MiKTeX/TeX Live). Die Engine wird automatisch erkannt.

## Verwendung

### Single File Mode (Backward Compatible)

#### Grundlegender Aufruf

```bash
python cli.py input.md output.docx
```

#### Mit Template

```bash
python cli.py input.md output.docx --template template.docx
```

**Hinweis**: DOCX-Templates werden nur für DOCX-Output verwendet. Bei PDF-Export wird ein Template ignoriert (mit entsprechender Info-Meldung).

#### Mit Profile

```bash
python cli.py input.md output.docx --profile report
```

#### Mit Template und Profile

```bash
python cli.py input.md output.docx --profile angebot --template templates/angebot.docx
```

#### Mit explizitem Pandoc-Pfad

Falls Pandoc nicht im PATH gefunden wird:

```bash
python cli.py input.md output.docx --pandoc-path "C:\Program Files\Pandoc\pandoc.exe"
```

#### Verbose Logging

```bash
python cli.py input.md output.docx --verbose
```

### PDF-Export

#### Einfacher PDF-Export

```bash
python cli.py input.md output.pdf --format pdf
```

#### PDF mit spezifischem Engine

```bash
python cli.py input.md output.pdf --format pdf --pdf-engine xelatex
python cli.py input.md output.pdf --format pdf --pdf-engine lualatex
python cli.py input.md output.pdf --format pdf --pdf-engine pdflatex
```

#### Mehrere Formate gleichzeitig

```bash
python cli.py input.md output --formats docx,pdf
# Erzeugt: output.docx und output.pdf
```

### Batch Mode

#### Grundlegende Batch-Konvertierung

```bash
python cli.py --batch input_folder output_folder
```

#### Rekursiv mit Unterordnern

```bash
python cli.py --batch input_folder output_folder --recursive
```

#### Mit Überschreiben bestehender Dateien

```bash
python cli.py --batch input_folder output_folder --overwrite
```

#### Mit Profile und Template

```bash
python cli.py --batch input_folder output_folder --profile report --template template.docx
```

#### Batch mit mehreren Formaten

```bash
python cli.py --batch input_folder output_folder --formats docx,pdf
# Erzeugt für jede .md Datei: .docx und .pdf
```

#### Kombiniert

```bash
python cli.py --batch input_folder output_folder --recursive --overwrite --profile angebot --formats docx,pdf
```

## YAML Frontmatter

Das Tool unterstützt YAML Frontmatter am Anfang von Markdown-Dateien für Metadaten:

```markdown
---
title: Mein Dokument
subtitle: Untertitel
author: Max Mustermann
version: 1.0
date: 2024-01-26
customer: Acme Corp
project: Projekt Alpha
---

# Inhalt

Hier beginnt der eigentliche Inhalt...
```

**Unterstützte Felder** (alle optional):
- `title`: Dokumenttitel
- `subtitle`: Untertitel
- `author`: Autor
- `version`: Versionsnummer
- `date`: Datum (Format: YYYY-MM-DD, oder leer für heute)
- `customer`: Kunde
- `project`: Projektname

Die Metadaten werden an Pandoc als Variablen übergeben und können in Templates verwendet werden.

**Hinweis**: Metadaten-Werte werden automatisch sanitisiert:
- Newlines (`\n`, `\r`) werden durch Leerzeichen ersetzt
- Führende/nachfolgende Leerzeichen werden entfernt
- Leere Werte werden ignoriert (nicht an Pandoc übergeben)

**Beispiel**: Siehe `examples/example_with_yaml.md`

## Preset-Profile

Das Tool bietet vordefinierte Profile für verschiedene Dokumenttypen:

### Verfügbare Profile

- **`report`** (Standard): Für Berichte mit TOC und nummerierten Abschnitten
- **`angebot`**: Für Angebote
- **`schulung`**: Für Schulungsunterlagen

### Profile-Features

Jedes Profile kann definieren:
- **Default-Template**: Standard-Template-Pfad
- **Pandoc-Argumente**: Zusätzliche Pandoc-Optionen (z.B. `--toc`, `--number-sections`)
- **Output-Naming**: Namensschema für Ausgabedateien (z.B. `{title}_Report.docx`)

### Profile verwenden

```bash
# Mit Standard-Profil
python cli.py input.md output.docx --profile report

# Profil mit eigenem Template
python cli.py input.md output.docx --profile angebot --template custom_template.docx
```

## Batch-Konvertierung

### Funktionsweise

- Konvertiert alle `*.md` Dateien in einem Ordner
- Output-Dateinamen:
  - Wenn YAML `title` vorhanden: `slug(title).docx`
  - Sonst: `original_dateiname.docx`
- Mit `--recursive`: Verarbeitet auch Unterordner
- Mit `--overwrite`: Überschreibt bestehende Dateien
- Ohne `--overwrite`: Überspringt existierende Dateien
- **Automatische Kollisionsbehandlung**: Wenn mehrere Dateien zum gleichen Output-Namen führen (z.B. gleicher Titel), werden automatisch eindeutige Namen erzeugt: `name.docx`, `name_2.docx`, `name_3.docx`, etc.

### Beispiel

```bash
# Einfache Batch-Konvertierung
python cli.py --batch ./docs ./output

# Rekursiv mit Überschreiben
python cli.py --batch ./docs ./output --recursive --overwrite

# Mit Profile
python cli.py --batch ./docs ./output --profile report --recursive
```

### Batch-Ergebnis

Am Ende wird eine Zusammenfassung ausgegeben:
```
Batch conversion complete: 15 successful, 2 skipped, 0 failed
```

## Konfiguration

### Umgebungsvariablen

- `PANDOC_PATH`: Pfad zur Pandoc-Executable (optional)
- `MD_CONVERTER_TEMPLATE`: Standard-Template-Pfad (optional)

Beispiel:
```bash
set PANDOC_PATH=C:\Program Files\Pandoc\pandoc.exe
set MD_CONVERTER_TEMPLATE=examples\template.docx
```

### Konfigurationsdatei

Die Datei `config.py` kann angepasst werden, um Standardwerte zu setzen.

## Projektstruktur

```
/
├─ converter/
│  ├─ __init__.py
│  ├─ pandoc_wrapper.py        # Kapselt Pandoc-Aufrufe
│  ├─ converter_service.py     # Logik md → docx
│  ├─ frontmatter.py           # YAML Frontmatter lesen/validieren
│  ├─ profiles.py              # Presets + Default-Config
│  ├─ batch_service.py         # Batch-Konvertierung
│  ├─ paths.py                 # Pfad-/Datei-Utilities
│  └─ errors.py                # Eigene Fehlerklassen
├─ cli.py                      # Kommandozeilen-Interface
├─ config.py                   # Konfiguration (Pandoc-Pfad, Template)
├─ requirements.txt
├─ README.md
├─ examples/
│  ├─ example.md
│  ├─ example_with_yaml.md     # Beispiel mit YAML Frontmatter
│  └─ template.docx (optional)
└─ tests/
   ├─ test_frontmatter.py
   ├─ test_profiles.py
   ├─ test_batch_service.py
   ├─ test_cli_args.py
   └─ test_paths.py
```

## Tests

Das Projekt enthält Unit-Tests mit pytest:

```bash
# Alle Tests ausführen
pytest

# Mit Verbose-Output
pytest -v

# Spezifische Test-Datei
pytest tests/test_frontmatter.py

# Mit Coverage (falls pytest-cov installiert)
pytest --cov=converter
```

### Test-Abdeckung

- ✅ YAML Frontmatter Parser (mit/ohne Frontmatter, ungültig, edge cases)
- ✅ Profile-Defaults und Override-Mechanik
- ✅ Batch-Service: Dateifilterung, Naming, overwrite/skip, recursive, Kollisionsbehandlung
- ✅ CLI Argument Parsing: Modi korrekt erkannt, Fehlermeldungen
- ✅ Pfad-Utilities (slugify, etc.)
- ✅ Metadata Sanitizing (Newlines, Leerzeichen, leere Werte)
- ✅ PDF-Engine-Erkennung und PDF-Konvertierung

**Hinweis**: Pandoc-Aufrufe werden in Tests gemockt (keine echte Pandoc-Abhängigkeit im Testlauf).

## Fehlerbehandlung

Das Tool gibt klare Fehlermeldungen aus:

- **Pandoc nicht gefunden**: Installationshinweis wird angezeigt
- **PDF-Engine nicht gefunden**: Installationshinweis für LaTeX-Distribution wird angezeigt
- **Ungültige Eingabedatei**: Datei existiert nicht oder ist nicht lesbar
- **Frontmatter-Fehler**: YAML-Frontmatter konnte nicht geparst werden
- **Profile-Fehler**: Profil existiert nicht oder ist ungültig
- **Konvertierungsfehler**: Detaillierte Fehlermeldung von Pandoc

### Troubleshooting PDF-Export

**Problem**: `PDFEngineNotFoundError: No PDF engine (LaTeX) found`

**Lösung**:
1. Installieren Sie eine LaTeX-Distribution (siehe Voraussetzungen)
2. Stellen Sie sicher, dass die PDF-Engine im PATH verfügbar ist:
   ```bash
   xelatex --version  # sollte funktionieren
   ```
3. Falls die Engine installiert, aber nicht im PATH ist:
   - Windows: Fügen Sie den LaTeX-Bin-Ordner zum System-PATH hinzu
   - Linux/macOS: Überprüfen Sie die Installation

**Problem**: PDF-Konvertierung schlägt fehl

**Lösung**:
- Prüfen Sie die Pandoc-Logs (--verbose)
- Versuchen Sie einen anderen PDF-Engine: `--pdf-engine lualatex`
- Stellen Sie sicher, dass alle benötigten LaTeX-Pakete installiert sind

## Beispiele

### Beispiel 1: Einfache Konvertierung

```bash
python cli.py examples/example.md output.docx
```

### Beispiel 2: Mit YAML Frontmatter

```bash
python cli.py examples/example_with_yaml.md output.docx --profile report
```

### Beispiel 3: Batch mit Template

```bash
python cli.py --batch ./markdown_docs ./word_docs --template corporate_template.docx --recursive
```

### Beispiel 4: Angebot mit eigenem Template

```bash
python cli.py angebot.md angebot.docx --profile angebot --template templates/angebot.docx
```

### Beispiel 5: PDF-Export

```bash
python cli.py dokument.md dokument.pdf --format pdf
```

### Beispiel 6: Mehrere Formate gleichzeitig

```bash
python cli.py dokument.md output --formats docx,pdf
# Erzeugt: output.docx und output.pdf
```

### Beispiel 7: Batch mit PDF

```bash
python cli.py --batch ./docs ./output --formats docx,pdf --recursive
```

## Entwicklung

### Code-Qualität

- Klar getrennte Verantwortlichkeiten
- Typ-Hints für alle Funktionen
- Docstrings für öffentliche Funktionen
- Logging auf INFO/ERROR-Level
- Unit-Tests für Kernlogik

### Erweiterungen

Diese Liste dient nur als technische Gedankenstütze.
Es besteht kein Anspruch auf Umsetzung oder Weiterentwicklung.

- GUI-Interface
- Installer / Packaging
- Config-YAML Support (optional)

## Backward Compatibility

Das Tool bleibt vollständig rückwärtskompatibel. Der ursprüngliche Aufruf funktioniert weiterhin:

```bash
python cli.py input.md output.docx
```

Alle neuen Features sind optional und brechen bestehende Workflows nicht.

## Verbesserungen (Changelog)

### Metadata Sanitizing
- Metadaten-Werte werden automatisch bereinigt (Newlines entfernt, Leerzeichen getrimmt)
- Leere Metadaten-Werte werden ignoriert
- Verbesserte Robustheit bei der Übergabe an Pandoc

### Logging-Verbesserungen
- Pandoc-Command wird nur bei DEBUG-Level vollständig geloggt
- INFO-Level zeigt kompakte Zusammenfassung (Format, Input, Output)
- Klarere Hinweise bei Template-Verwendung mit PDF

### Metadaten-Transparenz
- DEBUG-Logging zeigt an, wenn explizite Metadaten Frontmatter-Werte überschreiben
- Bessere Nachvollziehbarkeit bei Metadaten-Konflikten

### Batch-Kollisionsschutz
- Automatische Behandlung von Output-Namenskollisionen
- Eindeutige Dateinamen werden automatisch generiert (`name.docx`, `name_2.docx`, etc.)

## License

MIT License

This software is provided "as is", without warranty of any kind.
