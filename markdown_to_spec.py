#!/usr/bin/env python3
"""Convert README.md into a docx_create.py spec.json (python-docx)."""
import json
import re
import sys

def inline_runs(text):
    """Split text into runs handling **bold**, `code`, and @url:`...`."""
    runs = []
    # normalize @url:`https://...` -> keep the url text only
    text = re.sub(r'@url:`([^`]+)`', r'\1', text)
    # tokenize by **bold** and `code`
    pattern = re.compile(r'(\*\*.+?\*\*|`[^`]+`)')
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            runs.append({"text": text[pos:m.start()]})
        seg = m.group(0)
        if seg.startswith("**") and seg.endswith("**"):
            runs.append({"text": seg[2:-2], "bold": True})
        elif seg.startswith("`") and seg.endswith("`"):
            runs.append({"text": seg[1:-1]})
        pos = m.end()
    if pos < len(text):
        runs.append({"text": text[pos:]})
    return runs

def clean_plain(text):
    return re.sub(r'@url:`([^`]+)`', r'\1', text)

def clean_inline(text):
    """Remove markdown emphasis markers for plain-text contexts (lists, cells)."""
    t = re.sub(r'@url:`([^`]+)`', r'\1', text)
    t = re.sub(r'\*\*(.+?)\*\*', r'\1', t)   # **bold** -> text
    t = t.replace('`', '')                   # `code` -> code text
    return t

def main(md_path, spec_path):
    lines = open(md_path, encoding="utf-8").read().splitlines()
    blocks = []
    i = 0
    n = len(lines)

    def is_block_line(stripped):
        if stripped in ("", "---"):
            return True
        if stripped.startswith("```"):
            return True
        if stripped.startswith("#"):
            return True
        if stripped.startswith("|"):
            return True
        if stripped.startswith("- ") or stripped.startswith("* "):
            return True
        if re.match(r'^\d+\.\s', stripped):
            return True
        if re.match(r'!\[', stripped):
            return True
        return False

    para_buf = []
    def flush_para():
        nonlocal para_buf
        if para_buf:
            blocks.append({"type": "paragraph", "runs": inline_runs(" ".join(para_buf))})
            para_buf = []

    while i < n:
        line = lines[i].rstrip()
        stripped = line.strip()

        # block boundaries flush any accumulated paragraph first
        if is_block_line(stripped):
            flush_para()

        if stripped == "": i += 1; continue
        if stripped == "---": i += 1; continue
        # image
        m = re.match(r'!\[[^\]]*\]\(([^)]+)\)', stripped)
        if m:
            blocks.append({"type": "image", "path": m.group(1), "width_mm": 170})
            i += 1; continue
        # code fence
        if stripped.startswith("```"):
            code = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            for cl in code:
                blocks.append({"type": "paragraph", "runs": [{"text": cl or " "}]})
            continue
        # heading
        hm = re.match(r'^(#{1,6})\s+(.*)', stripped)
        if hm:
            blocks.append({"type": "heading", "level": len(hm.group(1)), "text": clean_plain(hm.group(2))})
            i += 1; continue
        # table block (header row immediately followed by divider row of --|--)
        if stripped.startswith("|") and i + 1 < n and re.match(r'^\s*\|[\s:|-]+\|', lines[i+1]):
            header = [c.strip() for c in stripped.strip("|").split("|")]
            j = i + 2
            rows = []
            while j < n and lines[j].strip().startswith("|"):
                cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                rows.append(cells)
                j += 1
            blocks.append({"type": "table", "header": [clean_inline(c) for c in header],
                           "rows": [[clean_inline(c) for c in row] for row in rows],
                           "style": "Light Grid Accent 1", "header_bold": True})
            i = j; continue
        # bullet list (accumulate consecutive)
        if stripped.startswith("- ") or stripped.startswith("* "):
            items = []
            while i < n:
                s = lines[i].strip()
                if s.startswith("- ") or s.startswith("* "):
                    items.append(clean_inline(s[2:].strip()))
                    i += 1
                else:
                    break
            blocks.append({"type": "bullet_list", "items": items})
            continue
        # numbered list
        if re.match(r'^\d+\.\s', stripped):
            items = []
            while i < n and re.match(r'^\d+\.\s', lines[i].strip()):
                items.append(clean_inline(re.sub(r'^\d+\.\s', '', lines[i].strip())))
                i += 1
            blocks.append({"type": "numbered_list", "items": items})
            continue
        # plain paragraph line: buffer for multi-line paragraph grouping
        para_buf.append(stripped)
        i += 1

    flush_para()

    spec = {
        "page": {"width_mm": 215.9, "height_mm": 279.4,
                 "margins_mm": {"top": 20, "bottom": 20, "left": 22, "right": 22}},
        "header": "MBAX 6418 — Assignment 1 · Sentiment & Emotion Classification of Amazon Reviews",
        "footer_page_numbers": True,
        "blocks": blocks,
    }
    with open(spec_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)
    print(f"wrote {spec_path}: {len(blocks)} blocks")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
