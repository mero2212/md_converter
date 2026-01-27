# Hardening Audit

## Findings (P0/P1/P2)
- P1 `cli.py:42` --formats parsing silently dropped invalid/empty entries, allowing unexpected outputs without clear errors. Fix: `cli.py:42`.
- P1 `cli.py:321` batch mode did not validate input/output directories or creation errors, risking crashes or confusing failures. Fix: `cli.py:331`.
- P1 `converter/batch_service.py:76` output path type/permissions were not validated, leading to unhandled OSError on mkdir or file path collisions. Fix: `converter/batch_service.py:81`.
- P1 `converter/converter_service.py:117` output path could be a directory and output dir creation errors were not handled, causing subprocess failures without clear messaging. Fix: `converter/converter_service.py:120` and `converter/converter_service.py:135`.
- P1 `converter/frontmatter.py:94` UTF-8 BOM/CRLF and empty values were not normalized, and malformed YAML lines were silently ignored. Fix: `converter/frontmatter.py:96`, `converter/frontmatter.py:178`, `converter/frontmatter.py:215`.
- P2 `converter/pandoc_wrapper.py:270` error messages could lose useful stdout context when stderr was empty. Fix: `converter/pandoc_wrapper.py:273`.
- P2 `converter/batch_service.py:127` existing outputs in non-overwrite runs could be treated as collisions and renamed instead of skipped. Fix: `converter/batch_service.py:132`.

## Fixes Applied
- CLI format parsing now rejects invalid values, trims/normalizes input, and returns consistent errors. (`cli.py:42`)
- Batch mode pre-validates input/output directories and handles output dir creation failures. (`cli.py:331`)
- Output path validation and directory creation errors are handled with clear ConversionError/InvalidFileError messages. (`converter/converter_service.py:120`, `converter/converter_service.py:135`)
- Batch service validates output paths, handles mkdir errors, and resolves name collisions deterministically while honoring overwrite/skip. (`converter/batch_service.py:81`, `converter/batch_service.py:132`)
- Frontmatter parser handles UTF-8 BOM, CRLF line endings, empty values, and malformed YAML lines with FrontmatterError. (`converter/frontmatter.py:96`, `converter/frontmatter.py:178`)
- Pandoc error handling now falls back to stdout when stderr is empty. (`converter/pandoc_wrapper.py:273`)

## Tests
- Run all tests:
  - `pytest -q`

- Focused tests:
  - `pytest -q tests/test_format_parsing.py`
  - `pytest -q tests/test_frontmatter.py`
  - `pytest -q tests/test_pandoc_wrapper_errors.py`
  - `pytest -q tests/test_batch_collisions.py`
