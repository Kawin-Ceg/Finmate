#!/usr/bin/env python3
"""
Generate FinMate_Full_Documentation.html from all docs markdown files.
Open the HTML in a browser, then File → Print → Save as PDF.

Usage:
    cd docs
    python generate_pdf.py
"""

import os
import re
from pathlib import Path

DOCS_DIR = Path(__file__).parent

DOC_ORDER = [
    "FinMate_Full_Documentation.md",
    "FinMate_Architecture.md",
    "FinMate_API_Documentation.md",
    "FinMate_Database_Documentation.md",
    "FinMate_ML_Documentation.md",
    "FinMate_User_Guide.md",
    "FinMate_Developer_Guide.md",
]

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    line-height: 1.65;
    color: #1a202c;
    background: #fff;
    max-width: 900px;
    margin: 0 auto;
    padding: 40px 48px;
}
h1 { font-size: 28px; color: #1a202c; margin: 48px 0 16px; border-bottom: 3px solid #4F46E5; padding-bottom: 10px; }
h2 { font-size: 20px; color: #2d3748; margin: 36px 0 12px; border-bottom: 1.5px solid #e2e8f0; padding-bottom: 6px; }
h3 { font-size: 16px; color: #4a5568; margin: 24px 0 8px; }
h4 { font-size: 14px; color: #4a5568; margin: 18px 0 6px; }
p { margin: 8px 0; }
ul, ol { margin: 8px 0 8px 24px; }
li { margin: 3px 0; }
code {
    font-family: 'Consolas', 'Courier New', monospace;
    background: #f0f4f8;
    padding: 2px 5px;
    border-radius: 3px;
    font-size: 11.5px;
    color: #4a1d96;
}
pre {
    background: #1e293b;
    color: #e2e8f0;
    padding: 16px 20px;
    border-radius: 6px;
    overflow-x: auto;
    margin: 12px 0;
    font-size: 11px;
    line-height: 1.5;
}
pre code {
    background: transparent;
    color: #e2e8f0;
    padding: 0;
    font-size: 11px;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    font-size: 12px;
}
th {
    background: #4F46E5;
    color: white;
    padding: 8px 12px;
    text-align: left;
    font-weight: 600;
}
td {
    padding: 7px 12px;
    border-bottom: 1px solid #e2e8f0;
}
tr:nth-child(even) td { background: #f8fafc; }
blockquote {
    border-left: 4px solid #4F46E5;
    padding: 8px 16px;
    background: #f0f4ff;
    margin: 12px 0;
    border-radius: 0 4px 4px 0;
}
a { color: #4F46E5; text-decoration: none; }
hr { border: none; border-top: 2px solid #e2e8f0; margin: 32px 0; }
.doc-separator {
    page-break-before: always;
    border-top: 4px solid #4F46E5;
    margin: 60px 0 40px;
    padding-top: 20px;
}
.doc-title {
    font-size: 22px;
    font-weight: 700;
    color: #4F46E5;
    margin-bottom: 8px;
}
.cover {
    text-align: center;
    padding: 100px 0 80px;
    border-bottom: 3px solid #4F46E5;
    margin-bottom: 48px;
}
.cover h1 { border: none; font-size: 42px; color: #4F46E5; }
.cover p { font-size: 16px; color: #718096; margin: 8px 0; }
.cover .badge {
    display: inline-block;
    background: #4F46E5;
    color: white;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 13px;
    margin: 4px;
}
@media print {
    body { max-width: 100%; padding: 20px 24px; }
    pre { page-break-inside: avoid; }
    h1, h2, h3 { page-break-after: avoid; }
    table { page-break-inside: avoid; }
    .doc-separator { page-break-before: always; }
}
"""


def md_to_html_simple(md_text):
    """
    Minimal Markdown-to-HTML converter for documentation content.
    Handles: headings, code blocks, tables, bold, inline code, horizontal rules, links, lists.
    """
    lines = md_text.split('\n')
    html_lines = []
    in_code_block = False
    code_lang = ""
    in_table = False
    table_header_done = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Fenced code blocks
        if line.strip().startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_lang = line.strip()[3:].strip()
                html_lines.append('<pre><code>')
            else:
                in_code_block = False
                html_lines.append('</code></pre>')
            i += 1
            continue

        if in_code_block:
            # Escape HTML in code blocks
            line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            html_lines.append(line)
            i += 1
            continue

        # Horizontal rule
        if re.match(r'^---+$', line.strip()) or re.match(r'^\*\*\*+$', line.strip()):
            if in_table:
                html_lines.append('</tbody></table>')
                in_table = False
            html_lines.append('<hr>')
            i += 1
            continue

        # Table rows
        if line.strip().startswith('|') and '|' in line[1:]:
            # Skip separator rows like |---|---|
            if re.match(r'^\|[-\s:|]+\|', line.strip()):
                i += 1
                continue
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            if not in_table:
                in_table = True
                table_header_done = False
                html_lines.append('<table><thead><tr>')
                for c in cells:
                    html_lines.append(f'<th>{inline_md(c)}</th>')
                html_lines.append('</tr></thead><tbody>')
                table_header_done = True
            else:
                html_lines.append('<tr>')
                for c in cells:
                    html_lines.append(f'<td>{inline_md(c)}</td>')
                html_lines.append('</tr>')
            i += 1
            continue
        elif in_table:
            html_lines.append('</tbody></table>')
            in_table = False

        # Headings
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            level = len(m.group(1))
            text = inline_md(m.group(2))
            # Create anchor id
            anchor = re.sub(r'[^a-z0-9\-]', '', text.lower().replace(' ', '-'))
            html_lines.append(f'<h{level} id="{anchor}">{text}</h{level}>')
            i += 1
            continue

        # Unordered list item
        m = re.match(r'^(\s*)[*\-]\s+(.*)', line)
        if m:
            text = inline_md(m.group(2))
            html_lines.append(f'<li>{text}</li>')
            i += 1
            continue

        # Ordered list item
        m = re.match(r'^\d+\.\s+(.*)', line)
        if m:
            text = inline_md(m.group(1))
            html_lines.append(f'<li>{text}</li>')
            i += 1
            continue

        # Blockquote
        m = re.match(r'^>\s*(.*)', line)
        if m:
            html_lines.append(f'<blockquote>{inline_md(m.group(1))}</blockquote>')
            i += 1
            continue

        # Empty line
        if not line.strip():
            html_lines.append('<p></p>')
            i += 1
            continue

        # Regular paragraph
        html_lines.append(f'<p>{inline_md(line)}</p>')
        i += 1

    if in_table:
        html_lines.append('</tbody></table>')
    if in_code_block:
        html_lines.append('</code></pre>')

    return '\n'.join(html_lines)


def inline_md(text):
    """Convert inline markdown: bold, italic, code, links."""
    # Escape HTML
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # Inline code
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    # Links
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)
    return text


def main():
    print("Generating FinMate_Full_Documentation.html ...")

    body_parts = []

    # Cover page
    body_parts.append("""
<div class="cover">
  <h1>FinMate</h1>
  <p style="font-size:20px;font-weight:600;color:#2d3748;margin:12px 0;">Complete Technical Documentation</p>
  <p>Version 1.0 &nbsp;·&nbsp; June 2025</p>
  <p style="margin-top:24px;">
    <span class="badge">React 19</span>
    <span class="badge">FastAPI</span>
    <span class="badge">PostgreSQL</span>
    <span class="badge">XGBoost</span>
    <span class="badge">TF-IDF</span>
  </p>
  <p style="margin-top:32px;color:#718096;font-size:12px;">
    AI-Powered Personal Finance Management Platform
  </p>
</div>
""")

    for doc_file in DOC_ORDER:
        path = DOCS_DIR / doc_file
        if not path.exists():
            print(f"  WARNING: {doc_file} not found, skipping")
            continue

        md_content = path.read_text(encoding='utf-8')
        html_content = md_to_html_simple(md_content)

        label = doc_file.replace("FinMate_", "").replace(".md", "").replace("_", " ")
        body_parts.append(f'<div class="doc-separator"><div class="doc-title">{label}</div></div>')
        body_parts.append(html_content)
        print(f"  Processed: {doc_file}")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>FinMate — Complete Technical Documentation</title>
  <style>
{CSS}
  </style>
</head>
<body>
{"".join(body_parts)}
</body>
</html>"""

    output_path = DOCS_DIR / "FinMate_Full_Documentation.html"
    output_path.write_text(html, encoding='utf-8')
    print(f"\nGenerated: {output_path}")
    print("\nTo create PDF:")
    print("  1. Open FinMate_Full_Documentation.html in Chrome or Edge")
    print("  2. Press Ctrl+P (Print)")
    print("  3. Destination: Save as PDF")
    print("  4. Paper size: A4, Margins: Minimum or Custom 10mm")
    print("  5. Save as FinMate_Full_Documentation.pdf")


if __name__ == "__main__":
    main()
