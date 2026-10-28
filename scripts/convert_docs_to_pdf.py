#!/usr/bin/env python3
"""
LCK Airport Documentation to PDF Converter.
Converts project READMEs and architecture specs to clean, styled PDFs with Mermaid diagrams and syntax highlighting.

Usage:
    python3 scripts/convert_docs_to_pdf.py
"""

import sys
import os
import re
import shutil
import subprocess

CSS_STYLE = """
@page {
    size: A4;
    margin: 18mm 15mm 18mm 15mm;
}

:root {
    --primary: #0969da;
    --text: #1f2328;
    --text-muted: #57606a;
    --border: #d0d7de;
    --border-muted: #eaeef2;
    --bg-subtle: #f6f8fa;
    --code-bg: #f6f8fa;
}

* {
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji", sans-serif;
    font-size: 13px;
    line-height: 1.6;
    color: var(--text);
    background-color: #ffffff;
    margin: 0;
    padding: 0;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}

h1, h2, h3, h4, h5, h6 {
    color: #0f172a;
    font-weight: 600;
    margin-top: 1.6em;
    margin-bottom: 0.5em;
    page-break-after: avoid;
    break-after: avoid;
}

h1 {
    font-size: 22px;
    padding-bottom: 0.35em;
    border-bottom: 2px solid #e2e8f0;
    margin-top: 0;
    color: #0f172a;
}

h2 {
    font-size: 17px;
    padding-bottom: 0.3em;
    border-bottom: 1px solid #e2e8f0;
    margin-top: 1.8em;
}

h3 {
    font-size: 14.5px;
    margin-top: 1.4em;
}

h4 {
    font-size: 13px;
}

p, ul, ol, dl {
    margin-top: 0;
    margin-bottom: 11px;
}

li {
    margin-bottom: 4px;
}

li > p {
    margin-bottom: 4px;
}

a {
    color: var(--primary);
    text-decoration: none;
}

table {
    border-collapse: collapse;
    width: 100%;
    margin-top: 12px;
    margin-bottom: 16px;
    font-size: 12px;
}

thead {
    display: table-header-group;
}

tr {
    page-break-inside: avoid;
    break-inside: avoid;
}

table th, table td {
    padding: 7px 11px;
    border: 1px solid var(--border);
    text-align: left;
    vertical-align: top;
}

table th {
    background-color: var(--bg-subtle);
    font-weight: 600;
    color: #0f172a;
}

table tr:nth-child(even) {
    background-color: #fcfcfd;
}

blockquote {
    margin: 12px 0 16px 0;
    padding: 8px 14px;
    color: var(--text-muted);
    border-left: 4px solid var(--primary);
    background-color: #f8fafc;
    border-radius: 0 4px 4px 0;
    page-break-inside: avoid;
    break-inside: avoid;
}

code {
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
    font-size: 11.5px;
    padding: 0.15em 0.35em;
    margin: 0;
    background-color: rgba(175, 184, 193, 0.2);
    border-radius: 4px;
}

pre {
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
    font-size: 11px;
    line-height: 1.45;
    background-color: var(--code-bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 10px 12px;
    white-space: pre-wrap;
    word-break: break-word;
    page-break-inside: avoid;
    break-inside: avoid;
}

pre code {
    background-color: transparent;
    padding: 0;
    border-radius: 0;
    font-size: inherit;
    white-space: pre-wrap;
}

.codehilite {
    background-color: var(--code-bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    margin-bottom: 14px;
    page-break-inside: avoid;
    break-inside: avoid;
}

.codehilite pre {
    border: none;
    margin: 0;
}

.mermaid-wrapper {
    margin: 18px auto;
    padding: 14px;
    background: #ffffff;
    border: 1px solid var(--border-muted);
    border-radius: 8px;
    text-align: center;
    page-break-inside: avoid;
    break-inside: avoid;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.mermaid-wrapper svg {
    max-width: 100% !important;
    height: auto !important;
    display: inline-block;
}

hr {
    height: 1px;
    background-color: var(--border-muted);
    border: none;
    margin: 22px 0;
}

.doc-header {
    border-bottom: 2px solid #0969da;
    padding-bottom: 8px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.doc-header .doc-tag {
    font-size: 11px;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
}

.doc-footer {
    margin-top: 40px;
    padding-top: 10px;
    border-top: 1px solid #e2e8f0;
    font-size: 10px;
    color: #94a3b8;
    text-align: center;
}
"""

def render_md_file(md_path, mermaid_js_path="/tmp/mermaid.min.js"):
    import markdown
    from pygments.formatters import HtmlFormatter

    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    mermaid_blocks = []
    def mermaid_replacer(match):
        idx = len(mermaid_blocks)
        code = match.group(1).strip()
        mermaid_blocks.append(code)
        return f"\n\n<!--MERMAID_PLACEHOLDER_{idx}-->\n\n"

    pattern = re.compile(r'```mermaid[ \t]*\n(.*?)\n```', re.DOTALL)
    content = pattern.sub(mermaid_replacer, content)

    formatter = HtmlFormatter(style='friendly')
    pygments_css = formatter.get_style_defs('.codehilite')

    md = markdown.Markdown(
        extensions=[
            'extra',
            'codehilite',
            'toc',
            'sane_lists',
        ],
        extension_configs={
            'codehilite': {
                'guess_lang': False,
                'css_class': 'codehilite',
                'linenums': False,
            }
        }
    )
    body_html = md.convert(content)

    for idx, block in enumerate(mermaid_blocks):
        escaped_block = (
            block.replace('&', '&amp;')
                 .replace('<', '&lt;')
                 .replace('>', '&gt;')
        )
        mermaid_div = (
            f'<div class="mermaid-wrapper">'
            f'<pre class="mermaid">{escaped_block}</pre>'
            f'</div>'
        )
        body_html = body_html.replace(f'<!--MERMAID_PLACEHOLDER_{idx}-->', mermaid_div)
        body_html = body_html.replace(f'<p><!--MERMAID_PLACEHOLDER_{idx}--></p>', mermaid_div)

    mermaid_script = ""
    if os.path.exists(mermaid_js_path):
        mermaid_script = f"""
    <script src="file://{mermaid_js_path}"></script>
    <script>
        document.addEventListener("DOMContentLoaded", function() {{
            mermaid.initialize({{
                startOnLoad: true,
                theme: 'default',
                securityLevel: 'loose',
                flowchart: {{ useMaxWidth: true, htmlLabels: true }},
                sequence: {{ useMaxWidth: true, showSequenceNumbers: true }}
            }});
        }});
    </script>
        """

    basename = os.path.basename(md_path)
    title = os.path.splitext(basename)[0].replace('-', ' ').replace('_', ' ').title()

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
{CSS_STYLE}
{pygments_css}
    </style>
    {mermaid_script}
</head>
<body>
<div class="doc-header">
    <span class="doc-tag">LCK Airport Documentation</span>
    <span class="doc-tag">{basename}</span>
</div>

{body_html}

<div class="doc-footer">
    Chaudhary Charan Singh International Airport (LCK) • Generated Documentation
</div>
</body>
</html>
"""
    return full_html

def convert_single(md_path, pdf_path, chrome_bin="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
    os.makedirs(os.path.dirname(os.path.abspath(pdf_path)), exist_ok=True)
    tmp_html = f"/tmp/render_{os.path.basename(md_path)}.html"
    
    html = render_md_file(md_path)
    with open(tmp_html, 'w', encoding='utf-8') as f:
        f.write(html)
        
    cmd = [
        chrome_bin,
        "--headless",
        "--disable-gpu",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=3500",
        "--allow-file-access-from-files",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        tmp_html
    ]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
        size_kb = os.path.getsize(pdf_path) / 1024
        print(f"  [OK] {md_path} -> {pdf_path} ({size_kb:.1f} KB)")
        return True
    else:
        print(f"  [ERROR] Failed to generate {pdf_path}")
        print("STDERR:", res.stderr)
        return False

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    readme_files_dir = os.path.join(root, "readme_files")
    
    files = [
        (
            os.path.join(readme_files_dir, "backend.md"),
            os.path.join(readme_files_dir, "backend.pdf"),
            os.path.join(readme_files_dir, "pdf", "backend.pdf")
        ),
        (
            os.path.join(readme_files_dir, "frontend.md"),
            os.path.join(readme_files_dir, "frontend.pdf"),
            os.path.join(readme_files_dir, "pdf", "frontend.pdf")
        ),
        (
            os.path.join(readme_files_dir, "initial-requirement.md"),
            os.path.join(readme_files_dir, "initial-requirement.pdf"),
            os.path.join(readme_files_dir, "pdf", "initial-requirement.pdf")
        ),
        (
            os.path.join(root, "README.md"),
            os.path.join(root, "README.pdf"),
            os.path.join(readme_files_dir, "pdf", "project-overview-README.pdf")
        ),
        (
            os.path.join(root, "backend", "README.md"),
            os.path.join(root, "backend", "README.pdf"),
            os.path.join(readme_files_dir, "pdf", "backend-README.pdf")
        ),
        (
            os.path.join(root, "frontend", "README.md"),
            os.path.join(root, "frontend", "README.pdf"),
            os.path.join(readme_files_dir, "pdf", "frontend-README.pdf")
        ),
        (
            os.path.join(root, "data", "README.md"),
            os.path.join(root, "data", "README.pdf"),
            os.path.join(readme_files_dir, "pdf", "data-README.pdf")
        )
    ]

    print("Converting Markdown documentation to PDF...")
    for src, primary_dst, central_dst in files:
        if not os.path.exists(src):
            continue
        print(f"Converting {os.path.basename(src)}...")
        if convert_single(src, primary_dst):
            os.makedirs(os.path.dirname(central_dst), exist_ok=True)
            shutil.copy2(primary_dst, central_dst)

if __name__ == '__main__':
    main()
