"""
Service for importing documents from various formats into TipTap/ProseMirror JSON.
"""
import re
from io import BytesIO
from typing import Any
from uuid import uuid4

from docx import Document as DocxDocument
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph


class DocumentImporter:
    """Imports documents from various formats to TipTap JSON."""

    def import_docx(self, file_content: bytes) -> dict[str, Any]:
        """
        Import a .docx file and convert to TipTap/ProseMirror JSON format.

        Returns:
            dict with:
                - content: TipTap JSON document
                - sections: list of detected sections with metadata
                - metadata: document metadata (title, author, etc.)
        """
        doc = DocxDocument(BytesIO(file_content))

        # Extract metadata
        metadata = self._extract_metadata(doc)

        # Convert content to TipTap JSON
        content, sections = self._convert_to_tiptap(doc)

        return {
            "content": content,
            "sections": sections,
            "metadata": metadata,
        }

    def _extract_metadata(self, doc: DocxDocument) -> dict[str, Any]:
        """Extract document metadata."""
        core_props = doc.core_properties
        return {
            "title": core_props.title or "",
            "author": core_props.author or "",
            "subject": core_props.subject or "",
            "created": core_props.created.isoformat() if core_props.created else None,
            "modified": core_props.modified.isoformat() if core_props.modified else None,
            "keywords": core_props.keywords or "",
        }

    def _convert_to_tiptap(self, doc: DocxDocument) -> tuple[dict, list[dict]]:
        """
        Convert docx content to TipTap JSON format.

        Returns:
            tuple of (tiptap_document, sections_list)
        """
        content_nodes = []
        sections = []
        current_section = None
        section_counter = [0]  # Use list for mutable reference in nested function

        for element in doc.element.body:
            # Handle paragraphs
            if element.tag.endswith("p"):
                para = Paragraph(element, doc)
                node = self._convert_paragraph(para, sections, section_counter)
                if node:
                    content_nodes.append(node)

            # Handle tables
            elif element.tag.endswith("tbl"):
                table_node = self._convert_table(element, doc)
                if table_node:
                    content_nodes.append(table_node)

        # Build TipTap document structure
        tiptap_doc = {
            "type": "doc",
            "content": content_nodes,
        }

        return tiptap_doc, sections

    def _convert_paragraph(
        self, para: Paragraph, sections: list[dict], section_counter: list[int]
    ) -> dict | None:
        """Convert a paragraph to TipTap node."""
        text = para.text.strip()
        if not text:
            return None

        style_name = para.style.name if para.style else ""

        # Check if this is a heading
        if style_name.startswith("Heading"):
            level = self._get_heading_level(style_name)
            node_id = str(uuid4())[:8]

            # Extract section number if present (e.g., "1.2 Requirements")
            section_match = re.match(r"^(\d+(?:\.\d+)*)\s*[.:\-]?\s*(.+)$", text)
            if section_match:
                section_number = section_match.group(1)
                section_title = section_match.group(2)
            else:
                section_counter[0] += 1
                section_number = str(section_counter[0])
                section_title = text

            # Track section for later creation
            sections.append({
                "section_number": section_number,
                "title": section_title,
                "level": level,
                "prosemirror_node_id": node_id,
            })

            return {
                "type": "heading",
                "attrs": {
                    "level": level,
                    "id": node_id,
                },
                "content": self._convert_text_runs(para),
            }

        # Check for list items
        if self._is_list_item(para):
            return {
                "type": "bulletList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": self._convert_text_runs(para),
                            }
                        ],
                    }
                ],
            }

        # Check for numbered list
        if self._is_numbered_item(para):
            return {
                "type": "orderedList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": self._convert_text_runs(para),
                            }
                        ],
                    }
                ],
            }

        # Regular paragraph
        return {
            "type": "paragraph",
            "content": self._convert_text_runs(para),
        }

    def _convert_text_runs(self, para: Paragraph) -> list[dict]:
        """Convert paragraph runs to TipTap text nodes with marks."""
        nodes = []

        for run in para.runs:
            if not run.text:
                continue

            node = {"type": "text", "text": run.text}
            marks = []

            if run.bold:
                marks.append({"type": "bold"})
            if run.italic:
                marks.append({"type": "italic"})
            if run.underline:
                marks.append({"type": "underline"})
            if run.font.strike:
                marks.append({"type": "strike"})

            if marks:
                node["marks"] = marks

            nodes.append(node)

        # If no runs, create a single text node
        if not nodes and para.text:
            nodes.append({"type": "text", "text": para.text})

        return nodes

    def _convert_table(self, table_element, doc) -> dict | None:
        """Convert a table to TipTap table node."""
        rows = []

        for tr in table_element.findall(qn("w:tr")):
            cells = []
            for tc in tr.findall(qn("w:tc")):
                # Get text from all paragraphs in cell
                cell_text = []
                for p in tc.findall(qn("w:p")):
                    para = Paragraph(p, doc)
                    if para.text.strip():
                        cell_text.append(para.text.strip())

                cells.append({
                    "type": "tableCell",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": "\n".join(cell_text)}
                            ] if cell_text else [],
                        }
                    ],
                })

            if cells:
                rows.append({
                    "type": "tableRow",
                    "content": cells,
                })

        if rows:
            return {
                "type": "table",
                "content": rows,
            }

        return None

    def _get_heading_level(self, style_name: str) -> int:
        """Extract heading level from style name."""
        match = re.search(r"(\d+)", style_name)
        if match:
            level = int(match.group(1))
            return min(max(level, 1), 6)  # Clamp to 1-6
        return 1

    def _is_list_item(self, para: Paragraph) -> bool:
        """Check if paragraph is a bullet list item."""
        # Check for bullet character at start
        text = para.text.strip()
        if text.startswith(("•", "●", "○", "■", "▪", "-", "*")):
            return True

        # Check paragraph style
        if para.style and "List" in para.style.name:
            return True

        # Check for numbering XML
        pPr = para._element.find(qn("w:pPr"))
        if pPr is not None:
            numPr = pPr.find(qn("w:numPr"))
            if numPr is not None:
                return True

        return False

    def _is_numbered_item(self, para: Paragraph) -> bool:
        """Check if paragraph is a numbered list item."""
        text = para.text.strip()
        # Check for number pattern at start
        if re.match(r"^\d+[.)\]]\s", text):
            return True
        return False

    def merge_consecutive_lists(self, nodes: list[dict]) -> list[dict]:
        """Merge consecutive list items into single lists."""
        merged = []
        current_list = None
        current_list_type = None

        for node in nodes:
            if node["type"] in ("bulletList", "orderedList"):
                if current_list_type == node["type"]:
                    # Merge into current list
                    current_list["content"].extend(node["content"])
                else:
                    # Start new list
                    if current_list:
                        merged.append(current_list)
                    current_list = node
                    current_list_type = node["type"]
            else:
                # Non-list item
                if current_list:
                    merged.append(current_list)
                    current_list = None
                    current_list_type = None
                merged.append(node)

        # Don't forget the last list
        if current_list:
            merged.append(current_list)

        return merged
