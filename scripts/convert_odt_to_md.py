from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Iterable

from lxml import etree


NS = {
    "draw": "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0",
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "xlink": "http://www.w3.org/1999/xlink",
}

XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"


def normalize_whitespace(value: str) -> str:
    return re.sub(r"[ \t]+", " ", value).strip()


def escape_md(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|")


def render_inline(node: etree._Element) -> str:
    parts: list[str] = []
    if node.text:
        parts.append(node.text)

    for child in node:
        local = etree.QName(child).localname
        if local == "s":
            count = int(child.get(f"{{{NS['text']}}}c", "1"))
            parts.append(" " * count)
        elif local == "line-break":
            parts.append("  \n")
        elif local == "tab":
            parts.append("    ")
        elif local == "a":
            href = child.get(f"{{{NS['xlink']}}}href", "")
            label = normalize_whitespace(render_inline(child))
            parts.append(f"[{label or href}]({href})" if href else label)
        elif local == "span":
            parts.append(render_inline(child))
        elif local == "frame":
            image = child.find(".//draw:image", NS)
            if image is not None:
                href = image.get(f"{{{NS['xlink']}}}href", "")
                if href:
                    alt = normalize_whitespace("".join(child.itertext())) or Path(href).name
                    parts.append(f"![{alt}]({href})")
            else:
                parts.append(render_inline(child))
        else:
            parts.append(render_inline(child))

        if child.tail:
            parts.append(child.tail)

    return "".join(parts)


def render_paragraph(node: etree._Element) -> str:
    text = normalize_whitespace(render_inline(node))
    return text


def render_list(node: etree._Element, level: int = 0) -> list[str]:
    lines: list[str] = []
    indent = "  " * level

    for item in node.findall("text:list-item", NS):
        block_children = [child for child in item if etree.QName(child).localname != "list-header"]
        first_written = False

        for child in block_children:
            local = etree.QName(child).localname
            if local == "p":
                text = render_paragraph(child)
                if not text:
                    continue
                prefix = f"{indent}- " if not first_written else f"{indent}  "
                lines.append(prefix + text)
                first_written = True
            elif local == "list":
                nested = render_list(child, level + 1)
                lines.extend(nested)

        if not first_written and not any(etree.QName(child).localname == "list" for child in block_children):
            lines.append(f"{indent}-")

    return lines


def render_table(node: etree._Element) -> list[str]:
    rows: list[list[str]] = []
    for row in node.findall("table:table-row", NS):
        values: list[str] = []
        for cell in row.findall("table:table-cell", NS):
            repeat = int(cell.get(f"{{{NS['table']}}}number-columns-repeated", "1"))
            text = " ".join(
                filter(None, (render_paragraph(p) for p in cell.findall("text:p", NS)))
            )
            for _ in range(repeat):
                values.append(escape_md(text))
        if values:
            rows.append(values)

    if not rows:
        return []

    width = max(len(row) for row in rows)
    padded = [row + [""] * (width - len(row)) for row in rows]
    header = padded[0]
    separator = ["---"] * width
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    for row in padded[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return lines


def export_images(archive: zipfile.ZipFile, odt_path: Path) -> None:
    image_names = [name for name in archive.namelist() if name.startswith("Pictures/")]
    if not image_names:
        return

    out_dir = odt_path.with_name(f"{odt_path.stem}_assets")
    out_dir.mkdir(exist_ok=True)
    for image_name in image_names:
        target = out_dir / Path(image_name).name
        target.write_bytes(archive.read(image_name))


def rewrite_image_links(lines: Iterable[str], odt_path: Path) -> list[str]:
    image_dir = f"{odt_path.stem}_assets"
    rewritten: list[str] = []
    for line in lines:
        rewritten.append(re.sub(r"\((Pictures/[^)]+)\)", lambda m: f"({image_dir}/{Path(m.group(1)).name})", line))
    return rewritten


def convert_file(odt_path: Path) -> Path:
    with zipfile.ZipFile(odt_path) as archive:
        root = etree.fromstring(archive.read("content.xml"))
        export_images(archive, odt_path)

    body = root.find(".//office:text", NS)
    if body is None:
        raise ValueError(f"Could not find document body in {odt_path}")

    lines: list[str] = []
    for child in body:
        local = etree.QName(child).localname
        if local == "sequence-decls":
            continue
        if local == "h":
            level = int(child.get(f"{{{NS['text']}}}outline-level", "1"))
            text = render_paragraph(child)
            if text:
                lines.append(f"{'#' * max(1, min(level, 6))} {text}")
        elif local == "p":
            text = render_paragraph(child)
            if text:
                if set(text) == {"-"}:
                    lines.append("---")
                else:
                    lines.append(text)
        elif local == "list":
            lines.extend(render_list(child))
        elif local == "table":
            lines.extend(render_table(child))
        else:
            text = render_paragraph(child)
            if text:
                lines.append(text)

        if lines and lines[-1] != "":
            lines.append("")

    cleaned: list[str] = []
    blank = False
    for line in rewrite_image_links(lines, odt_path):
        if line == "":
            if not blank:
                cleaned.append(line)
            blank = True
        else:
            cleaned.append(line)
            blank = False

    output_path = odt_path.with_suffix(".md")
    output_path.write_text("\n".join(cleaned).strip() + "\n", encoding="utf-8")
    return output_path


def main() -> None:
    root = Path.cwd()
    odt_files = sorted(root.glob("*.odt"))
    if not odt_files:
        raise SystemExit("No .odt files found in the current directory.")

    for odt_path in odt_files:
        output_path = convert_file(odt_path)
        print(f"Converted {odt_path.name} -> {output_path.name}")


if __name__ == "__main__":
    main()
