"""Read XLSX and DOCX audit content using only the Python standard library.

The source Office files are ZIP/XML containers. These readers never extract
files to the source directory and never modify the input archives.
"""

from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree as ET


MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
CORE_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC_NS = "http://purl.org/dc/elements/1.1/"
DCTERMS_NS = "http://purl.org/dc/terms/"

X = f"{{{MAIN_NS}}}"
R = f"{{{REL_NS}}}"
PR = f"{{{PACKAGE_REL_NS}}}"
W = f"{{{WORD_NS}}}"
A = f"{{{DRAWING_NS}}}"

CELL_REFERENCE = re.compile(r"^([A-Z]+)([0-9]+)$")
BUILTIN_DATE_FORMAT_IDS = {
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    27,
    30,
    36,
    45,
    46,
    47,
    50,
    57,
}


class OfficeReadError(RuntimeError):
    """Raised when a required Office package cannot be parsed."""


@dataclass(frozen=True)
class CellValue:
    """One populated or formula-bearing worksheet cell."""

    reference: str
    row: int
    column: int
    value: Any
    data_type: str
    formula: str | None = None
    style_index: int | None = None
    number_format: str | None = None


@dataclass
class SheetData:
    """Read-only logical worksheet content."""

    name: str
    state: str
    rows: list[list[Any]] = field(default_factory=list)
    cells: list[CellValue] = field(default_factory=list)
    merged_ranges: list[str] = field(default_factory=list)
    comments: list[dict[str, str]] = field(default_factory=list)
    dimension: str | None = None

    @property
    def row_count(self) -> int:
        return max((cell.row for cell in self.cells), default=0)

    @property
    def column_count(self) -> int:
        return max((cell.column for cell in self.cells), default=0)

    @property
    def formula_count(self) -> int:
        return sum(cell.formula is not None for cell in self.cells)


@dataclass
class WorkbookData:
    """Workbook inventory and logical sheets."""

    path: Path
    sheets: list[SheetData]
    properties: dict[str, str]
    archive_entries: list[str]


@dataclass
class DocxData:
    """DOCX headings, paragraphs, tables, and package metadata."""

    path: Path
    headings: list[dict[str, str]]
    paragraphs: list[str]
    tables: list[list[list[str]]]
    properties: dict[str, str]
    comments: list[dict[str, str]]
    archive_entries: list[str]


def column_number(reference: str) -> int:
    """Convert an Excel cell reference to a one-based column number."""

    match = CELL_REFERENCE.match(reference.upper())
    if match is None:
        raise OfficeReadError(f"Invalid Excel cell reference: {reference}")
    result = 0
    for character in match.group(1):
        result = result * 26 + (ord(character) - ord("A") + 1)
    return result


def _read_xml(archive: zipfile.ZipFile, name: str) -> ET.Element:
    try:
        payload = archive.read(name)
    except KeyError as error:
        raise OfficeReadError(f"Office package is missing {name}") from error
    try:
        return ET.fromstring(payload)
    except ET.ParseError as error:
        raise OfficeReadError(f"Invalid XML in {name}: {error}") from error


def _optional_xml(
    archive: zipfile.ZipFile,
    name: str,
) -> ET.Element | None:
    try:
        payload = archive.read(name)
    except KeyError:
        return None
    try:
        return ET.fromstring(payload)
    except ET.ParseError as error:
        raise OfficeReadError(f"Invalid XML in {name}: {error}") from error


def _core_properties(archive: zipfile.ZipFile) -> dict[str, str]:
    root = _optional_xml(archive, "docProps/core.xml")
    if root is None:
        return {}
    keys = {
        f"{{{DC_NS}}}title": "title",
        f"{{{DC_NS}}}subject": "subject",
        f"{{{DC_NS}}}creator": "creator",
        f"{{{CORE_NS}}}keywords": "keywords",
        f"{{{DC_NS}}}description": "description",
        f"{{{CORE_NS}}}lastModifiedBy": "last_modified_by",
        f"{{{DCTERMS_NS}}}created": "created",
        f"{{{DCTERMS_NS}}}modified": "modified",
        f"{{{CORE_NS}}}category": "category",
    }
    properties: dict[str, str] = {}
    for element in root:
        key = keys.get(element.tag)
        if key and element.text:
            properties[key] = element.text.strip()
    return properties


def _resolve_target(base: str, target: str) -> str:
    base_path = PurePosixPath(base)
    if target.startswith("/"):
        return target.lstrip("/")
    parts: list[str] = []
    for part in (base_path.parent / target).parts:
        if part == "..":
            if parts:
                parts.pop()
        elif part not in {"", "."}:
            parts.append(part)
    return "/".join(parts)


def _relationships(
    archive: zipfile.ZipFile,
    rels_name: str,
    source_name: str,
) -> dict[str, tuple[str, str]]:
    root = _optional_xml(archive, rels_name)
    if root is None:
        return {}
    result = {}
    for relationship in root.findall(f"{PR}Relationship"):
        relationship_id = relationship.attrib.get("Id")
        target = relationship.attrib.get("Target")
        relationship_type = relationship.attrib.get("Type", "")
        if relationship_id and target:
            result[relationship_id] = (
                _resolve_target(source_name, target),
                relationship_type,
            )
    return result


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    root = _optional_xml(archive, "xl/sharedStrings.xml")
    if root is None:
        return []
    values: list[str] = []
    for item in root.findall(f"{X}si"):
        values.append(
            "".join(
                node.text or ""
                for node in item.iter()
                if node.tag == f"{X}t"
            )
        )
    return values


def _style_formats(
    archive: zipfile.ZipFile,
) -> tuple[list[int], dict[int, str]]:
    root = _optional_xml(archive, "xl/styles.xml")
    if root is None:
        return [], {}
    custom_formats: dict[int, str] = {}
    num_formats = root.find(f"{X}numFmts")
    if num_formats is not None:
        for item in num_formats.findall(f"{X}numFmt"):
            try:
                identifier = int(item.attrib["numFmtId"])
            except (KeyError, ValueError):
                continue
            custom_formats[identifier] = item.attrib.get("formatCode", "")
    style_ids: list[int] = []
    cell_xfs = root.find(f"{X}cellXfs")
    if cell_xfs is not None:
        for xf in cell_xfs.findall(f"{X}xf"):
            try:
                style_ids.append(int(xf.attrib.get("numFmtId", "0")))
            except ValueError:
                style_ids.append(0)
    return style_ids, custom_formats


def _looks_like_date_format(identifier: int, format_code: str) -> bool:
    if identifier in BUILTIN_DATE_FORMAT_IDS:
        return True
    without_literals = re.sub(r'"[^"]*"|\\.', "", format_code.casefold())
    return bool(re.search(r"(?<!\[)[dmyhss]", without_literals))


def _excel_datetime(value: float) -> str:
    # Excel's 1900 date system includes the historical fictitious leap day.
    base = datetime(1899, 12, 30)
    converted = base + timedelta(days=value)
    if converted.time() == datetime.min.time():
        return converted.date().isoformat()
    return converted.isoformat(sep=" ")


def _cell_value(
    cell: ET.Element,
    shared_strings: list[str],
    style_ids: list[int],
    custom_formats: dict[int, str],
) -> tuple[Any, str, int | None, str | None]:
    cell_type = cell.attrib.get("t", "n")
    style_index: int | None
    try:
        style_index = int(cell.attrib["s"]) if "s" in cell.attrib else None
    except ValueError:
        style_index = None
    number_format_id = (
        style_ids[style_index]
        if style_index is not None and style_index < len(style_ids)
        else 0
    )
    number_format = custom_formats.get(number_format_id)
    if number_format is None and number_format_id:
        number_format = f"BUILTIN_FORMAT_{number_format_id}"

    if cell_type == "inlineStr":
        inline = cell.find(f"{X}is")
        text = (
            ""
            if inline is None
            else "".join(
                node.text or ""
                for node in inline.iter()
                if node.tag == f"{X}t"
            )
        )
        return text, "string", style_index, number_format
    value_element = cell.find(f"{X}v")
    raw_value = value_element.text if value_element is not None else None
    if raw_value is None:
        return None, "blank", style_index, number_format
    if cell_type == "s":
        try:
            return (
                shared_strings[int(raw_value)],
                "string",
                style_index,
                number_format,
            )
        except (ValueError, IndexError) as error:
            raise OfficeReadError(
                f"Invalid shared-string index: {raw_value}"
            ) from error
    if cell_type in {"str", "e"}:
        return raw_value, "formula_string" if cell_type == "str" else "error", style_index, number_format
    if cell_type == "b":
        return raw_value == "1", "boolean", style_index, number_format
    try:
        numeric = float(raw_value)
    except ValueError:
        return raw_value, "string", style_index, number_format
    if (
        style_index is not None
        and _looks_like_date_format(
            number_format_id,
            custom_formats.get(number_format_id, ""),
        )
    ):
        return _excel_datetime(numeric), "date", style_index, number_format
    if numeric.is_integer():
        return int(numeric), "integer", style_index, number_format
    return numeric, "number", style_index, number_format


def _sheet_comments(
    archive: zipfile.ZipFile,
    sheet_name: str,
) -> list[dict[str, str]]:
    rels_path = (
        str(PurePosixPath(sheet_name).parent)
        + "/_rels/"
        + PurePosixPath(sheet_name).name
        + ".rels"
    )
    relationships = _relationships(archive, rels_path, sheet_name)
    comment_target = next(
        (
            target
            for target, relation_type in relationships.values()
            if relation_type.endswith("/comments")
        ),
        None,
    )
    if comment_target is None:
        return []
    root = _read_xml(archive, comment_target)
    authors = [
        element.text or ""
        for element in root.findall(f".//{X}authors/{X}author")
    ]
    result = []
    for comment in root.findall(f".//{X}comment"):
        text = "".join(
            node.text or ""
            for node in comment.iter()
            if node.tag == f"{X}t"
        )
        try:
            author = authors[int(comment.attrib.get("authorId", "0"))]
        except (ValueError, IndexError):
            author = ""
        result.append(
            {
                "cell": comment.attrib.get("ref", ""),
                "author": author,
                "text": text,
            }
        )
    return result


def read_xlsx(path: str | Path) -> WorkbookData:
    """Read workbook sheets, values, formulas, merges, comments, and state."""

    source = Path(path)
    if not source.is_file():
        raise OfficeReadError(f"Workbook does not exist: {source}")
    try:
        archive = zipfile.ZipFile(source)
    except (OSError, zipfile.BadZipFile) as error:
        raise OfficeReadError(f"Workbook does not open: {source}") from error
    with archive:
        workbook_root = _read_xml(archive, "xl/workbook.xml")
        relationships = _relationships(
            archive,
            "xl/_rels/workbook.xml.rels",
            "xl/workbook.xml",
        )
        shared_strings = _shared_strings(archive)
        style_ids, custom_formats = _style_formats(archive)
        sheets: list[SheetData] = []
        for sheet in workbook_root.findall(f".//{X}sheet"):
            name = sheet.attrib.get("name", "UNCLEAR")
            state = sheet.attrib.get("state", "visible")
            relationship_id = sheet.attrib.get(f"{R}id")
            if relationship_id not in relationships:
                raise OfficeReadError(
                    f"Worksheet relationship is missing for {name}"
                )
            sheet_path = relationships[relationship_id][0]
            root = _read_xml(archive, sheet_path)
            cells: list[CellValue] = []
            row_values: dict[int, dict[int, Any]] = {}
            for cell in root.findall(f".//{X}sheetData/{X}row/{X}c"):
                reference = cell.attrib.get("r")
                if not reference:
                    continue
                match = CELL_REFERENCE.match(reference.upper())
                if match is None:
                    continue
                row_number = int(match.group(2))
                column = column_number(reference)
                value, data_type, style_index, number_format = _cell_value(
                    cell,
                    shared_strings,
                    style_ids,
                    custom_formats,
                )
                formula_element = cell.find(f"{X}f")
                formula = (
                    formula_element.text
                    if formula_element is not None
                    else None
                )
                if value is not None or formula is not None:
                    row_values.setdefault(row_number, {})[column] = value
                    cells.append(
                        CellValue(
                            reference=reference,
                            row=row_number,
                            column=column,
                            value=value,
                            data_type=data_type,
                            formula=formula,
                            style_index=style_index,
                            number_format=number_format,
                        )
                    )
            max_row = max(row_values, default=0)
            max_column = max(
                (
                    max(values)
                    for values in row_values.values()
                    if values
                ),
                default=0,
            )
            rows = [
                [
                    row_values.get(row_number, {}).get(column)
                    for column in range(1, max_column + 1)
                ]
                for row_number in range(1, max_row + 1)
            ]
            merged_ranges = [
                item.attrib.get("ref", "")
                for item in root.findall(f".//{X}mergeCells/{X}mergeCell")
                if item.attrib.get("ref")
            ]
            dimension_element = root.find(f"{X}dimension")
            dimension = (
                dimension_element.attrib.get("ref")
                if dimension_element is not None
                else None
            )
            sheets.append(
                SheetData(
                    name=name,
                    state=state,
                    rows=rows,
                    cells=cells,
                    merged_ranges=merged_ranges,
                    comments=_sheet_comments(archive, sheet_path),
                    dimension=dimension,
                )
            )
        return WorkbookData(
            path=source,
            sheets=sheets,
            properties=_core_properties(archive),
            archive_entries=archive.namelist(),
        )


def _word_text(element: ET.Element) -> str:
    return "".join(
        node.text or ""
        for node in element.iter()
        if node.tag in {f"{W}t", f"{W}tab", f"{W}br"}
    ).strip()


def _docx_comments(archive: zipfile.ZipFile) -> list[dict[str, str]]:
    root = _optional_xml(archive, "word/comments.xml")
    if root is None:
        return []
    result = []
    for comment in root.findall(f"{W}comment"):
        result.append(
            {
                "id": comment.attrib.get(f"{W}id", ""),
                "author": comment.attrib.get(f"{W}author", ""),
                "date": comment.attrib.get(f"{W}date", ""),
                "text": _word_text(comment),
            }
        )
    return result


def read_docx(path: str | Path) -> DocxData:
    """Read headings, paragraphs, tables, properties, and comments."""

    source = Path(path)
    if not source.is_file():
        raise OfficeReadError(f"DOCX does not exist: {source}")
    try:
        archive = zipfile.ZipFile(source)
    except (OSError, zipfile.BadZipFile) as error:
        raise OfficeReadError(f"DOCX does not open: {source}") from error
    with archive:
        root = _read_xml(archive, "word/document.xml")
        headings: list[dict[str, str]] = []
        paragraphs: list[str] = []
        body = root.find(f"{W}body")
        if body is None:
            raise OfficeReadError("DOCX document body is missing")
        for paragraph in body.findall(f"{W}p"):
            text = _word_text(paragraph)
            if not text:
                continue
            paragraphs.append(text)
            style = paragraph.find(f"{W}pPr/{W}pStyle")
            style_name = (
                style.attrib.get(f"{W}val", "")
                if style is not None
                else ""
            )
            if style_name.casefold().startswith("heading"):
                headings.append({"style": style_name, "text": text})
        tables: list[list[list[str]]] = []
        for table in body.findall(f"{W}tbl"):
            rows: list[list[str]] = []
            for row in table.findall(f"{W}tr"):
                rows.append(
                    [_word_text(cell) for cell in row.findall(f"{W}tc")]
                )
            tables.append(rows)
        return DocxData(
            path=source,
            headings=headings,
            paragraphs=paragraphs,
            tables=tables,
            properties=_core_properties(archive),
            comments=_docx_comments(archive),
            archive_entries=archive.namelist(),
        )


__all__ = [
    "CellValue",
    "DocxData",
    "OfficeReadError",
    "SheetData",
    "WorkbookData",
    "column_number",
    "read_docx",
    "read_xlsx",
]
