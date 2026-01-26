# ROADMAP.md

Technische Verbesserungen und Refactoring-Aufgaben.

> Diese Liste dient als interne Gedankenstütze.
> Es besteht kein Anspruch auf Umsetzung oder Zeitplan.

---

## Kritische / Hohe Priorität

### 1. Output-Datei-Validierung nach Pandoc-Konvertierung
- **Datei**: `converter/pandoc_wrapper.py` (Zeilen 242-259)
- **Problem**: Nach erfolgreicher Pandoc-Ausführung wird nicht geprüft, ob die Output-Datei existiert und Inhalt hat
- **Risiko**: Pandoc könnte ohne Fehler laufen, aber eine leere/korrupte Datei erzeugen
- **Lösung**: Post-Conversion-Check hinzufügen

### 2. Format-Validierung extrahieren (DRY)
- **Datei**: `cli.py` (Zeilen 169-176 und 270-277)
- **Problem**: Identische Format-Parsing-Logik in `handle_single_conversion()` und `handle_batch_conversion()`
- **Lösung**: Gemeinsame Hilfsfunktion `_parse_and_validate_formats()` erstellen

### 3. Encoding-Fallback für Frontmatter-Parser
- **Datei**: `converter/frontmatter.py` (Zeile 96)
- **Problem**: Bei nicht-UTF8-Dateien crasht das Tool mit UnicodeDecodeError
- **Lösung**: Fallback auf latin-1 oder chardet-Detection

### 4. Import-Organisation korrigieren
- **Datei**: `converter/pandoc_wrapper.py` (Zeile 96)
- **Problem**: `import re` steht innerhalb von `_sanitize_metadata_value()` statt am Modulanfang
- **Lösung**: Import an Modulanfang verschieben

---

## Mittlere Priorität

### 5. SUPPORTED_FORMATS Konstante einführen
- **Dateien**: `cli.py`, `converter/pandoc_wrapper.py`
- **Problem**: `["docx", "pdf"]` ist an mehreren Stellen hardcoded
- **Lösung**: Zentrale Konstante in `config.py` oder eigenem Modul

### 6. Exception-Handling präzisieren
- **Dateien**: `converter/converter_service.py` (Zeile 156), `converter/batch_service.py` (Zeile 175)
- **Problem**: `except Exception` ist zu breit, fängt auch SystemExit/KeyboardInterrupt
- **Lösung**: Spezifische Exceptions abfangen

### 7. Type Hints korrigieren
- **Datei**: `converter/batch_service.py` (Zeile 23)
- **Problem**: `List[Tuple[Path, str]]` aber `md_file` ist manchmal str
- **Lösung**: Konsistente Typisierung durchsetzen

---

## Niedrige Priorität

### 8. Unused Imports entfernen
- `converter/frontmatter.py`: `date` importiert aber nicht verwendet
- `converter/profiles.py`: `Union` importiert aber nicht verwendet

### 9. Lazy Import in converter_service.py
- **Datei**: `converter/converter_service.py` (Zeile 120)
- **Problem**: `from converter.paths import get_output_filename` innerhalb der Funktion
- **Lösung**: An Modulanfang verschieben (falls keine zirkuläre Abhängigkeit)

---

## Zukünftige Überlegungen (nicht priorisiert)

- Enum für OutputFormat statt Strings
- Thread-Safety für Batch-Service bei paralleler Nutzung
- Chardet-Integration für automatische Encoding-Erkennung
- Validierung von Pandoc-Args in Profilen
