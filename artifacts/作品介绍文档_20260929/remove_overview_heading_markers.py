"""Remove Word's non-printing keep-with-next markers from overview headings."""

from pathlib import Path
import os

from docx import Document


ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = next((ROOT / "artifacts" / "作品介绍文档_20260929").glob("*系统概述.docx"))
SUBMISSION = ROOT / "参赛作品提交材料_20260929" / "06_系统概述" / "系统概述.docx"
HEADINGS = {"一  背景介绍", "二  主要功能", "三  作品特点"}


for path in (ORIGINAL, SUBMISSION):
    doc = Document(path)
    paragraphs = [p for p in doc.paragraphs if p.text in HEADINGS]
    if len(paragraphs) != 3 or {p.text for p in paragraphs} != HEADINGS:
        raise RuntimeError(f"Unexpected headings in {path}")
    for paragraph in paragraphs:
        paragraph.paragraph_format.keep_with_next = None

    temporary = path.with_name(f"{path.stem}.tmp.docx")
    doc.save(temporary)
    os.replace(temporary, path)
    print(f"Updated 3 headings: {path}")
