from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


DEFAULT_BASE_DIR = Path(__file__).resolve().parent
NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}
TITLE_PLACEHOLDER_TYPES = {"title", "ctrTitle", "subTitle"}
SLIDE_NAME_RE = re.compile(r"ppt/slides/slide(\d+)\.xml$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract slide titles and body text from all PPTX files in a directory."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_BASE_DIR / "ppts",
        help="Directory containing .pptx files. Defaults to ./ppts beside this script.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_BASE_DIR / "data" / "slides.json",
        help="Output JSON path. Defaults to ./data/slides.json beside this script.",
    )
    return parser.parse_args()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def iter_paragraph_text(paragraphs: Iterable[ET.Element]) -> list[str]:
    lines: list[str] = []

    for paragraph in paragraphs:
        parts: list[str] = []
        for node in paragraph.iter():
            node_name = local_name(node.tag)
            if node_name == "t" and node.text:
                parts.append(node.text)
            elif node_name == "br":
                parts.append("\n")

        line = "".join(parts).strip()
        if line:
            lines.append(line)

    return lines


def extract_shape_text(shape: ET.Element) -> str:
    tx_body = shape.find("p:txBody", NS)
    if tx_body is None:
        return ""

    paragraphs = tx_body.findall("a:p", NS)
    return "\n".join(iter_paragraph_text(paragraphs)).strip()


def extract_graphic_frame_text(graphic_frame: ET.Element) -> str:
    paragraphs = graphic_frame.findall(".//a:tbl//a:p", NS)
    return "\n".join(iter_paragraph_text(paragraphs)).strip()


def get_placeholder_type(shape: ET.Element) -> str | None:
    placeholder = shape.find("p:nvSpPr/p:nvPr/p:ph", NS)
    if placeholder is None:
        return None

    return placeholder.get("type", "body")


def collect_slide_items(container: ET.Element) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []

    for child in list(container):
        child_name = local_name(child.tag)

        if child_name == "sp":
            text = extract_shape_text(child)
            if not text:
                continue

            placeholder_type = get_placeholder_type(child)
            kind = "title" if placeholder_type in TITLE_PLACEHOLDER_TYPES else "body"
            items.append({"kind": kind, "text": text})
        elif child_name == "graphicFrame":
            text = extract_graphic_frame_text(child)
            if text:
                items.append({"kind": "body", "text": text})
        elif child_name == "grpSp":
            items.extend(collect_slide_items(child))

    return items


def parse_slide(xml_bytes: bytes) -> tuple[str, str]:
    root = ET.fromstring(xml_bytes)
    shape_tree = root.find("p:cSld/p:spTree", NS)
    if shape_tree is None:
        return "", ""

    items = collect_slide_items(shape_tree)
    title_parts = [item["text"] for item in items if item["kind"] == "title"]
    body_parts = [item["text"] for item in items if item["kind"] == "body"]

    if not title_parts and body_parts:
        title_parts = [body_parts[0]]
        body_parts = body_parts[1:]

    title = "\n".join(title_parts).strip()
    body = "\n\n".join(body_parts).strip()
    return title, body


def extract_ppt_records(pptx_path: Path) -> list[dict[str, str | int]]:
    records: list[dict[str, str | int]] = []

    with zipfile.ZipFile(pptx_path) as archive:
        slide_names = []
        for name in archive.namelist():
            match = SLIDE_NAME_RE.fullmatch(name)
            if match:
                slide_names.append((int(match.group(1)), name))

        for slide_number, slide_name in sorted(slide_names):
            title, body = parse_slide(archive.read(slide_name))
            records.append(
                {
                    "ppt文件名": pptx_path.name,
                    "页码": slide_number,
                    "标题": title,
                    "正文": body,
                }
            )

    return records


def main() -> int:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    output_path = args.output.resolve()

    if not input_dir.exists():
        print(f"未找到目录: {input_dir}")
        print("请先把 .pptx 文件放到输入目录中。")
        return 1

    pptx_files = sorted(input_dir.glob("*.pptx"))
    if not pptx_files:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("[]", encoding="utf-8")
        print(f"未找到 .pptx 文件，已输出空结果到: {output_path}")
        return 0

    all_records: list[dict[str, str | int]] = []
    for pptx_file in pptx_files:
        try:
            all_records.extend(extract_ppt_records(pptx_file))
        except zipfile.BadZipFile:
            print(f"跳过损坏或非标准的 PPTX 文件: {pptx_file.name}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(all_records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"处理完成，共提取 {len(all_records)} 条记录。")
    print(f"输入目录: {input_dir}")
    print(f"输出文件: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
