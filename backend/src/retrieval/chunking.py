import re
from typing import List, Dict, Any


def extract_markdown_tables(content: str) -> List[Dict[str, Any]]:
    """
    Extracts markdown tables and retains row-level context.
    """
    tables = []
    lines = content.split("\n")
    current_table = []
    in_table = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            in_table = True
            current_table.append(stripped)
        else:
            if in_table and len(current_table) >= 2:
                tables.append("\n".join(current_table))
            in_table = False
            current_table = []

    if in_table and len(current_table) >= 2:
        tables.append("\n".join(current_table))

    parsed = []
    for t_str in tables:
        t_lines = t_str.split("\n")
        if len(t_lines) < 2:
            continue
        headers = [h.strip() for h in t_lines[0].split("|")[1:-1]]
        # line 1 is separator |---|---|
        rows = []
        for r_line in t_lines[2:]:
            cols = [c.strip() for c in r_line.split("|")[1:-1]]
            if len(cols) == len(headers):
                row_dict = dict(zip(headers, cols))
                rows.append(row_dict)
        parsed.append({
            "raw_table": t_str,
            "headers": headers,
            "rows": rows
        })

    return parsed


def chunk_document(doc_id: str, title: str, content: str, chunk_size: int = 500, overlap: int = 100) -> List[Dict[str, Any]]:
    """
    Splits markdown document into semantic chunks, preserving tables as indivisible chunks.
    """
    chunks = []
    sections = re.split(r'\n(?=#{1,4}\s)', content)

    for sec_idx, section in enumerate(sections):
        sec_lines = section.strip().split("\n")
        header = sec_lines[0] if sec_lines and sec_lines[0].startswith("#") else f"Section {sec_idx+1}"
        body = section.strip()

        # If section contains tables, keep table as atomic chunk
        tables = extract_markdown_tables(body)
        for t_idx, t in enumerate(tables):
            # Create row-level semantic strings for lexical search
            row_summaries = []
            for r in t["rows"]:
                row_summaries.append(" | ".join([f"{k}: {v}" for k, v in r.items()]))

            chunks.append({
                "chunk_id": f"{doc_id}_s{sec_idx}_table_{t_idx}",
                "doc_id": doc_id,
                "doc_title": title,
                "header": header,
                "text": f"Table in {title} ({header}):\n{t['raw_table']}\nRow Details: " + " ; ".join(row_summaries),
                "is_table": True,
                "raw_table": t["raw_table"]
            })

        # Text chunking
        # Remove raw tables from text body to avoid duplication
        clean_body = body
        for t in tables:
            clean_body = clean_body.replace(t["raw_table"], "")

        words = clean_body.split()
        if not words:
            continue

        step = chunk_size - overlap if chunk_size > overlap else chunk_size
        for w_idx in range(0, len(words), step):
            chunk_words = words[w_idx:w_idx + chunk_size]
            c_text = " ".join(chunk_words).strip()
            if len(c_text) > 20:
                chunks.append({
                    "chunk_id": f"{doc_id}_s{sec_idx}_w{w_idx}",
                    "doc_id": doc_id,
                    "doc_title": title,
                    "header": header,
                    "text": f"[{title} - {header}]\n{c_text}",
                    "is_table": False
                })

    return chunks

