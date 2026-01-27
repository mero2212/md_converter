# Template-Anleitung

Anleitung zum Erstellen von DOCX-Templates für den Markdown Converter.

## Grundprinzip

Pandoc verwendet das Template als **Referenz-Dokument**:
- Formatvorlagen (Styles) werden übernommen
- Kopf-/Fußzeilen bleiben erhalten
- Seiteneinstellungen werden übernommen
- Der **Inhalt** des Templates wird ignoriert

## Standard-Template erzeugen

```bash
# Pandoc's Standard-Template exportieren
pandoc -o template_basis.docx --print-default-data-file reference.docx
```

Dieses Template enthält alle benötigten Styles und kann als Ausgangspunkt dienen.

## Wichtige Formatvorlagen

### Pflicht-Styles

| Style-Name | Verwendung | Pandoc-Mapping |
|------------|------------|----------------|
| `Title` | Dokumenttitel | YAML: `title` |
| `Subtitle` | Untertitel | YAML: `subtitle` |
| `Author` | Autor | YAML: `author` |
| `Date` | Datum | YAML: `date` |
| `Heading 1` | Überschrift Ebene 1 | `# Heading` |
| `Heading 2` | Überschrift Ebene 2 | `## Heading` |
| `Heading 3` | Überschrift Ebene 3 | `### Heading` |
| `Body Text` | Normaler Absatz | Fließtext |
| `First Paragraph` | Erster Absatz nach Überschrift | Fließtext |

### Optionale Styles

| Style-Name | Verwendung |
|------------|------------|
| `Abstract` | Zusammenfassung (YAML: `abstract`) |
| `Block Text` | Eingerückte Zitate (`>`) |
| `Source Code` | Code-Blöcke (```) |
| `Verbatim Char` | Inline-Code (`) |
| `Compact` | Listen-Elemente |
| `Table` | Tabellen |
| `Image Caption` | Bildunterschriften |
| `Table Caption` | Tabellenüberschriften |
| `Figure` | Bilder |
| `TOC Heading` | Inhaltsverzeichnis-Überschrift |

## Kopf- und Fußzeilen

### Logo in Kopfzeile

1. Template in Word öffnen
2. Doppelklick auf Kopfzeile
3. Logo einfügen (Einfügen → Bilder)
4. Position wählen (links, mitte, rechts)
5. Größe anpassen
6. Speichern

### Dynamische Felder

In Kopf-/Fußzeilen können Word-Felder verwendet werden:

| Feld | Einfügen über |
|------|---------------|
| Seitenzahl | Einfügen → Seitenzahl |
| Datum | Einfügen → Schnellbausteine → Feld → Date |
| Dateiname | Einfügen → Schnellbausteine → Feld → FileName |

**Hinweis**: YAML-Metadaten (Titel, Autor) können NICHT direkt in Kopf-/Fußzeilen eingefügt werden - diese werden nur im Dokumentkörper ersetzt.

## Seiteneinstellungen

Das Template definiert:

- **Papierformat**: A4, Letter, etc.
- **Seitenränder**: Oben, Unten, Links, Rechts
- **Ausrichtung**: Hochformat, Querformat
- **Spalten**: Ein- oder mehrspaltig

Diese Einstellungen unter: Layout → Seitenränder / Ausrichtung / Größe

## Schritt-für-Schritt: Eigenes Template

### 1. Basis erstellen

```bash
# Standard-Template als Basis
pandoc -o mein_template.docx --print-default-data-file reference.docx
```

### 2. In Word anpassen

1. `mein_template.docx` in Word öffnen
2. **Formatvorlagen anpassen** (Start → Formatvorlagen → Rechtsklick → Ändern)
   - Schriftart, Größe, Farbe
   - Abstände, Einzüge
   - Nummerierung für Überschriften
3. **Kopfzeile bearbeiten**
   - Logo einfügen
   - Firmenname, Seitenzahl
4. **Fußzeile bearbeiten**
   - Copyright, Datum, Seitenzahl
5. **Seitenränder** anpassen
6. Speichern

### 3. Testen

```bash
# Mit Beispiel-Markdown testen
mdconv beispiel.md test_output.docx --template mein_template.docx
```

### 4. Im Projekt verwenden

```bash
# Template in local/templates/ ablegen
cp mein_template.docx local/templates/bericht.docx

# Oder direkt verwenden
mdconv input.md output.docx --template local/templates/bericht.docx
```

## Beispiel: Corporate Template

### Anforderungen

- Logo oben links
- Firmenname oben rechts
- Seitenzahl unten mitte
- Corporate-Schriftart (z.B. Arial)
- Blaue Überschriften (#003366)

### Umsetzung

1. **Heading 1** anpassen:
   - Schriftart: Arial, 16pt, Fett
   - Farbe: #003366
   - Abstand vor: 24pt, nach: 12pt

2. **Body Text** anpassen:
   - Schriftart: Arial, 11pt
   - Zeilenabstand: 1.15

3. **Kopfzeile**:
   - Links: Logo (Höhe: 1.5cm)
   - Rechts: Firmenname, Arial 10pt

4. **Fußzeile**:
   - Mitte: Seitenzahl

## Fehlerbehebung

### Styles werden nicht übernommen

**Problem**: Formatierung im Output stimmt nicht mit Template überein.

**Lösung**:
- Prüfen ob Style-Namen exakt stimmen (Groß-/Kleinschreibung!)
- Pandoc-Version prüfen (`pandoc --version`)
- Template mit `--print-default-data-file` neu erstellen

### Logo erscheint nicht

**Problem**: Logo in Kopfzeile fehlt im Output.

**Lösung**:
- Logo muss **in der Kopfzeile** sein, nicht im Dokumentkörper
- Logo als eingebettetes Bild, nicht als Verknüpfung
- Template-Pfad prüfen

### Inhaltsverzeichnis fehlt

**Problem**: TOC wird nicht generiert trotz `--toc`.

**Lösung**:
- `TOC Heading` Style muss existieren
- Mindestens eine Überschrift im Dokument
- Pandoc-Argument `--toc` prüfen

## Referenzen

- [Pandoc User's Guide - Templates](https://pandoc.org/MANUAL.html#templates)
- [Pandoc DOCX Output](https://pandoc.org/MANUAL.html#options-affecting-specific-writers)
