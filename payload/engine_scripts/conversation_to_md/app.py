"""
Streamlit UI for the Conversation-to-Markdown converter.

Minimal, functional interface:
  - Upload ZIP
  - Set options
  - Convert
  - Download result
"""

from __future__ import annotations

import io
import shutil
import tempfile
import zipfile
from pathlib import Path

import streamlit as st

from conversation_to_md.core.pipeline import convert_zip_bytes
from conversation_to_md.core.renderer import RenderOptions


def main() -> None:
    st.set_page_config(page_title="Conversation to Markdown", layout="centered")
    st.title("Conversation to Markdown")
    st.caption(
        "Convert AI chat exports (ChatGPT, Claude, Gemini, Grok) into clean Markdown files."
    )

    # --- File Upload ---
    uploaded_file = st.file_uploader(
        "Upload a ZIP export",
        type=["zip"],
        help="Drop your exported conversation archive here.",
    )

    # --- Options ---
    st.subheader("Options")
    col1, col2 = st.columns(2)
    with col1:
        include_timestamps = st.checkbox("Include timestamps", value=True)
        include_system = st.checkbox("Include system messages", value=False)
    with col2:
        emoji_headers = st.checkbox("Emoji role headers", value=True)
        output_structure = st.selectbox(
            "Output structure",
            ["structured", "flat"],
            help="Structured groups by provider; flat puts all files together.",
        )

    # --- Convert ---
    if uploaded_file is not None:
        if st.button("Convert", type="primary"):
            options = RenderOptions(
                include_timestamps=include_timestamps,
                include_system_messages=include_system,
                emoji_headers=emoji_headers,
                output_structure=output_structure,
            )

            progress_area = st.empty()
            status_log: list[str] = []

            def on_progress(msg: str) -> None:
                status_log.append(msg)
                progress_area.text("\n".join(status_log))

            # Convert
            output_dir = Path(tempfile.mkdtemp(prefix="conv_output_"))
            try:
                data = uploaded_file.read()
                written, source = convert_zip_bytes(
                    data, output_dir, options, progress_callback=on_progress
                )

                if not written:
                    st.warning(
                        "No conversations found in the uploaded file. "
                        "The format may not be recognized."
                    )
                    return

                st.success(
                    f"Converted {len(written)} conversation(s) from **{source}** export."
                )

                # Package output as downloadable ZIP
                zip_buffer = _zip_directory(output_dir)
                st.download_button(
                    label=f"Download {len(written)} Markdown files (ZIP)",
                    data=zip_buffer,
                    file_name="conversations_md.zip",
                    mime="application/zip",
                )

                # Preview first conversation
                if written:
                    with st.expander("Preview first conversation"):
                        preview_text = written[0].read_text(encoding="utf-8")
                        st.markdown(
                            f"```markdown\n{preview_text[:3000]}\n```"
                        )
            finally:
                shutil.rmtree(output_dir, ignore_errors=True)


def _zip_directory(directory: Path) -> bytes:
    """Create an in-memory ZIP of a directory's contents."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(directory)
                zf.write(file_path, arcname)
    buffer.seek(0)
    return buffer.getvalue()


if __name__ == "__main__":
    main()
