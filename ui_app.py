"""Streamlit UI for Markdown to DOCX/PDF conversion (local only)."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple

import streamlit as st

from converter.converter_service import ConverterService
from converter.errors import (
    ConversionError,
    FrontmatterError,
    MermaidRenderError,
    PandocNotFoundError,
    PDFEngineNotFoundError,
    ProfileError,
)
from converter.profiles import list_profiles


def _write_upload_to_temp(upload, suffix: str) -> Path:
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        temp_file.write(upload.getbuffer())
    finally:
        temp_file.close()
    return Path(temp_file.name)


def _convert_once(
    converter: ConverterService,
    input_path: Path,
    output_format: str,
    template_path: Optional[Path],
    profile_name: Optional[str],
    pdf_engine: Optional[str],
    output_name: str,
) -> Tuple[str, bytes]:
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / output_name
        converter.convert(
            input_path=str(input_path),
            output_path=str(output_path),
            template_path=str(template_path) if template_path else None,
            profile_name=profile_name,
            output_format=output_format,
            pdf_engine=pdf_engine,
        )
        return output_path.name, output_path.read_bytes()


def main() -> None:
    st.set_page_config(page_title="Markdown → DOCX/PDF", page_icon="📝")
    st.title("Markdown → DOCX/PDF (lokal)")
    st.caption("Offline-UX für das bestehende Konvertierungstool.")

    md_upload = st.file_uploader(
        "Markdown-Datei (.md)",
        type=["md"],
        accept_multiple_files=False,
    )

    template_upload = st.file_uploader(
        "Optionales DOCX-Template",
        type=["docx"],
        accept_multiple_files=False,
    )

    pandoc_path_input = st.text_input(
        "Pandoc-Pfad (leer = PATH)",
        value="",
        help="Leer lassen, um pandoc aus dem PATH zu verwenden.",
    )

    output_choice = st.radio(
        "Output",
        options=["docx", "pdf", "beides"],
        horizontal=True,
    )

    profile_options = ["(kein Profil)"] + list_profiles()
    profile_choice = st.selectbox("Profil", options=profile_options)

    pdf_engine_choice = st.selectbox(
        "PDF Engine",
        options=["auto", "xelatex", "lualatex", "pdflatex"],
        index=0,
    )

    st.caption("Hinweis: DOCX-Template wird bei PDF ignoriert.")

    convert_clicked = st.button(
        "Konvertieren",
        disabled=md_upload is None,
        use_container_width=True,
    )

    if "results" not in st.session_state:
        st.session_state["results"] = {}

    if convert_clicked:
        st.session_state["results"] = {}
        input_path: Optional[Path] = None
        template_path: Optional[Path] = None
        try:
            input_path = _write_upload_to_temp(md_upload, suffix=".md")
            template_path = (
                _write_upload_to_temp(template_upload, suffix=".docx")
                if template_upload is not None
                else None
            )

            pandoc_path = pandoc_path_input.strip() or None
            converter = ConverterService(pandoc_path=pandoc_path)

            profile_name = None if profile_choice == "(kein Profil)" else profile_choice
            pdf_engine = None if pdf_engine_choice == "auto" else pdf_engine_choice

            input_stem = Path(md_upload.name).stem or "document"

            formats = []
            if output_choice == "beides":
                formats = ["docx", "pdf"]
            else:
                formats = [output_choice]

            results: Dict[str, Tuple[str, bytes]] = {}
            for output_format in formats:
                output_name = f"{input_stem}.{output_format}"
                use_template = template_path if output_format == "docx" else None
                name, data = _convert_once(
                    converter=converter,
                    input_path=input_path,
                    output_format=output_format,
                    template_path=use_template,
                    profile_name=profile_name,
                    pdf_engine=pdf_engine,
                    output_name=output_name,
                )
                results[output_format] = (name, data)

            st.session_state["results"] = results
            st.success("Konvertierung erfolgreich.")

        except PandocNotFoundError as e:
            st.error("Pandoc nicht gefunden. Bitte installieren oder Pfad angeben.")
            with st.expander("Details"):
                st.write(str(e))
        except PDFEngineNotFoundError as e:
            st.error("LaTeX Engine fehlt. Bitte MiKTeX/TeX Live installieren.")
            with st.expander("Details"):
                st.write(str(e))
        except FrontmatterError as e:
            st.error("Frontmatter-Fehler in der Markdown-Datei.")
            with st.expander("Details"):
                st.write(str(e))
        except ProfileError as e:
            st.error("Profil-Fehler. Bitte Profil prüfen.")
            with st.expander("Details"):
                st.write(str(e))
        except ConversionError as e:
            st.error("Konvertierung fehlgeschlagen.")
            with st.expander("Details"):
                st.write(str(e))
        except MermaidRenderError as e:
            st.error("Mermaid-Diagramme konnten nicht gerendert werden.")
            with st.expander("Details"):
                st.write(str(e))
        except Exception as e:
            st.error("Unerwarteter Fehler.")
            with st.expander("Details"):
                st.write(str(e))
        finally:
            if input_path and input_path.exists():
                input_path.unlink()
            if template_path and template_path.exists():
                template_path.unlink()

    results = st.session_state.get("results", {})
    if results:
        st.subheader("Downloads")
        for output_format, (filename, data) in results.items():
            st.download_button(
                label=f"{output_format.upper()} herunterladen",
                data=data,
                file_name=filename,
            )


if __name__ == "__main__":
    main()
