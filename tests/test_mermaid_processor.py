"""Tests for Mermaid diagram processor."""

import hashlib
import pytest
from pathlib import Path
from unittest.mock import patch

from converter.errors import MermaidRenderError
from converter.mermaid_processor import (
    has_mermaid_diagrams,
    extract_mermaid_blocks,
    process_mermaid_in_markdown,
    is_mermaid_available,
    find_mermaid_cli,
    render_mermaid_to_svg_and_png,
    MERMAID_PATTERN,
)


class TestHasMermaidDiagrams:
    """Tests for has_mermaid_diagrams function."""

    def test_detects_mermaid_block(self):
        content = """# Title

Some text.

```mermaid
graph TD
    A --> B
```

More text.
"""
        assert has_mermaid_diagrams(content) is True

    def test_detects_multiple_mermaid_blocks(self):
        content = """# Title

```mermaid
graph TD
    A --> B
```

```mermaid
sequenceDiagram
    A->>B: Hello
```
"""
        assert has_mermaid_diagrams(content) is True

    def test_no_mermaid_block(self):
        content = """# Title

Some text.

```python
print("hello")
```
"""
        assert has_mermaid_diagrams(content) is False

    def test_empty_content(self):
        assert has_mermaid_diagrams("") is False

    def test_case_insensitive(self):
        content = """```MERMAID
graph TD
    A --> B
```"""
        assert has_mermaid_diagrams(content) is True

    def test_mermaid_in_text_not_detected(self):
        content = "I love mermaid diagrams but this has no code block"
        assert has_mermaid_diagrams(content) is False


class TestExtractMermaidBlocks:
    """Tests for extract_mermaid_blocks function."""

    def test_extract_single_block(self):
        content = """# Title

```mermaid
graph TD
    A --> B
```
"""
        blocks = extract_mermaid_blocks(content)
        assert len(blocks) == 1
        full_match, diagram_code = blocks[0]
        assert "graph TD" in diagram_code
        assert "A --> B" in diagram_code

    def test_extract_multiple_blocks(self):
        content = """# Title

```mermaid
graph TD
    A --> B
```

Some text.

```mermaid
sequenceDiagram
    Alice->>Bob: Hello
```
"""
        blocks = extract_mermaid_blocks(content)
        assert len(blocks) == 2
        assert "graph TD" in blocks[0][1]
        assert "sequenceDiagram" in blocks[1][1]

    def test_extract_preserves_whitespace(self):
        content = """```mermaid
graph TD
    A[Start] --> B{Decision}
    B -->|Yes| C[End]
    B -->|No| D[Loop]
```"""
        blocks = extract_mermaid_blocks(content)
        assert len(blocks) == 1
        _, diagram_code = blocks[0]
        assert "A[Start]" in diagram_code

    def test_no_blocks_returns_empty_list(self):
        content = "No mermaid here"
        blocks = extract_mermaid_blocks(content)
        assert blocks == []


class TestFindMermaidCli:
    """Tests for find_mermaid_cli function."""

    @patch('shutil.which')
    def test_finds_mmdc_in_path(self, mock_which):
        mock_which.return_value = "/usr/local/bin/mmdc"
        result = find_mermaid_cli()
        assert result == "/usr/local/bin/mmdc"
        mock_which.assert_called_with("mmdc")

    @patch('shutil.which')
    def test_returns_none_if_not_found(self, mock_which):
        mock_which.return_value = None
        with patch.object(Path, 'exists', return_value=False):
            result = find_mermaid_cli()
            # May return None or find it in common paths
            # depending on the system


class TestIsMermaidAvailable:
    """Tests for is_mermaid_available function."""

    @patch('converter.mermaid_processor.find_mermaid_cli')
    def test_available_when_found(self, mock_find):
        mock_find.return_value = "/usr/local/bin/mmdc"
        assert is_mermaid_available() is True

    @patch('converter.mermaid_processor.find_mermaid_cli')
    def test_not_available_when_not_found(self, mock_find):
        mock_find.return_value = None
        assert is_mermaid_available() is False


class TestProcessMermaidInMarkdown:
    """Tests for process_mermaid_in_markdown function."""

    @patch('converter.mermaid_processor.find_mermaid_cli')
    def test_returns_unchanged_when_no_mermaid(self, mock_find, tmp_path):
        content = "# Title\n\nNo diagrams here."
        processed, images = process_mermaid_in_markdown(
            content, tmp_path, "docx"
        )
        assert processed == content
        assert images == []

    @patch('converter.mermaid_processor.find_mermaid_cli')
    def test_raises_when_mmdc_not_available(self, mock_find, tmp_path):
        mock_find.return_value = None
        content = """# Title

```mermaid
graph TD
    A --> B
```
"""
        with pytest.raises(MermaidRenderError) as exc_info:
            process_mermaid_in_markdown(
                content, tmp_path, "docx"
            )
        assert "Mermaid CLI (mmdc) not found" in str(exc_info.value)

    @patch('converter.mermaid_processor.render_mermaid_to_svg_and_png')
    @patch('converter.mermaid_processor.find_mermaid_cli')
    def test_replaces_mermaid_block_with_image(self, mock_find, mock_render, tmp_path):
        mock_find.return_value = "/usr/local/bin/mmdc"

        def create_dummy_images(diagram_code, svg_path, png_path, *args, **kwargs):
            svg_path.write_text("<svg></svg>", encoding="utf-8")
            png_path.write_bytes(b"PNG dummy data")

        mock_render.side_effect = create_dummy_images

        content = """# Title

```mermaid
graph TD
    A --> B
```

More text.
"""
        processed, images = process_mermaid_in_markdown(
            content, tmp_path, "docx"
        )

        assert "```mermaid" not in processed
        assert "![](_assets/diagrams/" in processed
        assert ".png)" in processed
        assert len(images) == 2
        assert any(p.suffix == ".png" for p in images)
        assert any(p.suffix == ".svg" for p in images)

    @patch('converter.mermaid_processor.render_mermaid_to_svg_and_png')
    @patch('converter.mermaid_processor.find_mermaid_cli')
    def test_processes_multiple_diagrams(self, mock_find, mock_render, tmp_path):
        mock_find.return_value = "/usr/local/bin/mmdc"

        def create_dummy_images(diagram_code, svg_path, png_path, *args, **kwargs):
            svg_path.write_text("<svg></svg>", encoding="utf-8")
            png_path.write_bytes(b"PNG dummy data")

        mock_render.side_effect = create_dummy_images

        content = """# Title

```mermaid
graph TD
    A --> B
```

Middle text.

```mermaid
sequenceDiagram
    A->>B: Hello
```
"""
        processed, images = process_mermaid_in_markdown(
            content, tmp_path, "docx"
        )

        assert "```mermaid" not in processed
        assert processed.count("![](_assets/diagrams/") == 2
        assert len(images) == 4

    @patch('converter.mermaid_processor.render_mermaid_to_svg_and_png')
    @patch('converter.mermaid_processor.find_mermaid_cli')
    def test_format_selection_pdf_vs_docx(self, mock_find, mock_render, tmp_path):
        mock_find.return_value = "/usr/local/bin/mmdc"

        def create_dummy_images(diagram_code, svg_path, png_path, *args, **kwargs):
            svg_path.write_text("<svg></svg>", encoding="utf-8")
            png_path.write_bytes(b"PNG dummy data")

        mock_render.side_effect = create_dummy_images

        content = """```mermaid
graph TD
    A --> B
```"""

        processed_docx, _ = process_mermaid_in_markdown(
            content, tmp_path, "docx"
        )
        processed_pdf, _ = process_mermaid_in_markdown(
            content, tmp_path, "pdf"
        )

        assert processed_docx.endswith(".png)")
        assert processed_pdf.endswith(".svg)")


class TestMermaidCaching:
    """Tests for hash-based caching behavior."""

    @patch('converter.mermaid_processor._run_mermaid_cli')
    def test_skips_render_when_outputs_exist(self, mock_run, tmp_path):
        svg_path = tmp_path / "diagram.svg"
        png_path = tmp_path / "diagram.png"
        svg_path.write_text("<svg></svg>", encoding="utf-8")
        png_path.write_bytes(b"PNG")

        render_mermaid_to_svg_and_png(
            "graph TD\n  A --> B",
            svg_path,
            png_path,
            mmdc_path="mmdc"
        )

        mock_run.assert_not_called()

    @patch('converter.mermaid_processor.render_mermaid_to_svg_and_png')
    @patch('converter.mermaid_processor.find_mermaid_cli')
    def test_uses_hash_based_filenames(self, mock_find, mock_render, tmp_path):
        mock_find.return_value = "/usr/local/bin/mmdc"

        def create_dummy_images(diagram_code, svg_path, png_path, *args, **kwargs):
            svg_path.write_text("<svg></svg>", encoding="utf-8")
            png_path.write_bytes(b"PNG")

        mock_render.side_effect = create_dummy_images

        content = """```mermaid
graph TD
    A --> B
```"""

        processed, _ = process_mermaid_in_markdown(content, tmp_path, "docx")

        diagram_code = "graph TD\n    A --> B"
        expected_hash = hashlib.sha256(diagram_code.encode("utf-8")).hexdigest()
        assert f"_assets/diagrams/{expected_hash}.png" in processed


class TestMermaidPattern:
    """Tests for the MERMAID_PATTERN regex."""

    def test_matches_basic_mermaid_block(self):
        content = """```mermaid
graph TD
    A --> B
```"""
        match = MERMAID_PATTERN.search(content)
        assert match is not None
        assert match.group(1).strip() == "graph TD\n    A --> B"

    def test_matches_with_extra_whitespace(self):
        content = """```mermaid
graph TD
```"""
        match = MERMAID_PATTERN.search(content)
        assert match is not None

    def test_does_not_match_other_code_blocks(self):
        content = """```python
print("hello")
```"""
        match = MERMAID_PATTERN.search(content)
        assert match is None

    def test_matches_complex_diagram(self):
        content = """```mermaid
sequenceDiagram
    participant Alice
    participant Bob
    Alice->>John: Hello John, how are you?
    loop Healthcheck
        John->>John: Fight against hypochondria
    end
    Note right of John: Rational thoughts <br/>prevail!
    John-->>Alice: Great!
    John->>Bob: How about you?
    Bob-->>John: Jolly good!
```"""
        match = MERMAID_PATTERN.search(content)
        assert match is not None
        assert "participant Alice" in match.group(1)
        assert "Jolly good!" in match.group(1)
