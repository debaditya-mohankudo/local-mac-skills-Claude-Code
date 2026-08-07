# Architecture and setup: vault → Documentation/Tools/VAULT_RAG.md
"""Vault RAG — semantic + FTS search over Obsidian vault. No API keys.

POC branch: ChromaDB replaced with TurboVec (turbovec.IdMapIndex).
Persistence: .tvim index file + .meta.json sidecar (id → file/section mapping).
"""
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import numpy as np
import turbovec
from llama_index.embeddings.ollama import OllamaEmbedding

from config import config as cfg
from tools.rag_core import load_index as _rag_load, save_index as _rag_save, query_index as _rag_query

# Mirrors the indexer's skip sets — keep in sync with tools/index_vault_sections.py
_SKIP_HEADINGS = {
    "contents", "related", "summary", "sources", "notes", "index",
    "overview", "introduction", "references", "see also", "links",
    "navigation", "tags", "metadata", "index terms",
}
_SKIP_FOLDERS = {".obsidian", "Tmp", ".git", "Cache", "Daily", "Weekly", "Monthly"}
_STOPWORDS = {
    "the", "and", "for", "that", "this", "with", "from", "have", "will",
    "been", "are", "was", "were", "not", "but", "into", "also", "than",
    "then", "when", "each", "more", "some", "such", "their", "there",
    "these", "they", "what", "which", "your", "can", "may", "per",
    "all", "any", "its", "our", "you", "has", "had", "use",
}


def _parse_frontmatter(text: str) -> dict:
    result = {"title": None, "tags": [], "created": None, "updated": None}
    if not text.startswith("---"):
        return result
    end = text.find("\n---", 3)
    if end == -1:
        return result
    fm = text[3:end]
    m = re.search(r"^title:\s*(.+)$", fm, re.MULTILINE)
    if m:
        result["title"] = m.group(1).strip().strip('"')
    for field in ("created", "updated"):
        m = re.search(rf"^{field}:\s*(.+)$", fm, re.MULTILINE)
        if m:
            result[field] = m.group(1).strip()
    m = re.search(r"^tags:\s*\[(.+?)\]", fm, re.MULTILINE)
    if m:
        result["tags"] = [t.strip().strip('"') for t in m.group(1).split(",")]
    else:
        in_tags = False
        for line in fm.splitlines():
            if re.match(r"^tags:\s*$", line):
                in_tags = True
                continue
            if in_tags:
                tm = re.match(r"^\s+-\s+(.+)$", line)
                if tm:
                    result["tags"].append(tm.group(1).strip())
                elif line and not line.startswith(" "):
                    break
    return result


def _extract_keywords(body: str, max_keywords: int = 30) -> str:
    body = re.sub(r"```.*?```", " ", body, flags=re.DOTALL)
    body = re.sub(r"`[^`]+`", " ", body)
    body = re.sub(r"https?://\S+", " ", body)
    body = re.sub(r"\[\[([^\]|#]+)[^\]]*\]\]", r"\1", body)
    inline_tags = re.findall(r"#([a-zA-Z][a-zA-Z0-9_-]*)", body)
    short_tokens = re.findall(r"\b(D\d{1,2}|H\d{1,2}|AD|MD)\b", body)
    hyphen_tokens = re.findall(r"\b([a-zA-Z][a-zA-Z0-9]*-\d+[a-zA-Z0-9]*)\b", body)
    body = re.sub(r"[|#*_~>\-]", " ", body)
    body = re.sub(r"[^\w\s/]", " ", body)
    seen: dict[str, int] = {}
    for tag in inline_tags:
        tok = tag.lower()
        if len(tok) >= 2:
            seen[tok] = seen.get(tok, 0) + 5
    for tok in short_tokens:
        seen[tok.lower()] = seen.get(tok.lower(), 0) + 5
    for tok in hyphen_tokens:
        tl = tok.lower()
        seen[tl] = seen.get(tl, 0) + 5
        tn = tl.replace("-", "")
        seen[tn] = seen.get(tn, 0) + 5
    for word in body.lower().split():
        word = word.strip("/")
        if len(word) >= 3 and word not in _STOPWORDS and not word.isdigit():
            seen[word] = seen.get(word, 0) + 1
    return ",".join(sorted(seen, key=lambda w: -seen[w])[:max_keywords])


def _extract_index_terms(text: str) -> str:
    m = re.search(r"^#{2,3}\s+Index Terms\s*\n(.*?)(?=^#{1,3}\s|\Z)", text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    if not m:
        return ""
    tokens = re.split(r"[|\n,]+", m.group(1))
    cleaned = []
    for tok in tokens:
        tok = tok.strip().strip("*_")
        if not tok:
            continue
        if ":" in tok:
            k, _, v = tok.partition(":")
            cleaned.extend([k.strip(), v.strip()])
        else:
            cleaned.append(tok)
    return ",".join(t for t in cleaned if t)


def _parse_file_sections(rel_path: str, text: str) -> list[dict]:
    """Parse a vault file into section dicts ready for SQLite upsert."""
    fm = _parse_frontmatter(text)
    index_terms = _extract_index_terms(text)
    tags_str = ",".join(fm["tags"])
    folder = str(Path(rel_path).parent)

    lines = text.splitlines()
    heading_positions = []
    for i, line in enumerate(lines):
        m = re.match(r"^(#{2,3})\s+(.+)$", line)
        if m:
            level = len(m.group(1))
            heading = m.group(2).strip()
            if heading.lower() not in _SKIP_HEADINGS:
                heading_positions.append((i, heading, level))

    sections = []
    now = datetime.utcnow().isoformat()
    for idx, (line_no, heading, level) in enumerate(heading_positions):
        next_line = heading_positions[idx + 1][0] if idx + 1 < len(heading_positions) else len(lines)
        body = "\n".join(lines[line_no + 1:next_line])
        kw = _extract_keywords(body)
        if index_terms:
            kw = f"{kw},{index_terms}" if kw else index_terms
        sections.append({
            "file": rel_path,
            "folder": folder,
            "title": fm["title"],
            "section": heading,
            "level": level,
            "tags": tags_str,
            "keywords": kw,
            "created": fm["created"],
            "updated": fm["updated"],
            "indexed_at": now,
        })
    return sections

EMBED_MODEL_NAME = "nomic-embed-text"

_META_PATH = cfg.vault_rag_tvim.with_suffix(".meta.json")


# ── helpers ──────────────────────────────────────────────────────────────────

def _get_embed_model() -> OllamaEmbedding:
    return OllamaEmbedding(model_name=EMBED_MODEL_NAME)


def _sqlite_sections() -> list[dict]:
    """Load all sections from vault_index.sqlite."""
    con = sqlite3.connect(str(cfg.vault_index_db))
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT id, file, section, title, tags, keywords FROM sections"
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def _load_index() -> tuple[turbovec.IdMapIndex, dict] | tuple[None, None]:
    index, meta = _rag_load(cfg.vault_rag_tvim, _META_PATH)
    return (index, meta) if index is not None else (None, None)


def _save_index(index: turbovec.IdMapIndex, meta: dict) -> None:
    _rag_save(index, meta, cfg.vault_rag_tvim, _META_PATH)


# ── MCP tools ─────────────────────────────────────────────────────────────────

def handle_index_vault(force: bool = False) -> str:
    """Build semantic index from vault_index.sqlite sections using local Ollama embeddings.

    Reads pre-chunked sections from the existing SQLite — no re-parsing needed.
    Stores index in iCloud as .tvim file. Pass force=True to rebuild from scratch.
    """
    if not force:
        index, meta = _load_index()
        if index is not None:
            return f"Index already has {len(index)} chunks. Pass force=True to rebuild."

    sections = [
        s for s in _sqlite_sections()
        if s["section"] and s["section"].strip()
    ]
    if not sections:
        return "No sections found in vault_index.sqlite."

    embed_model = _get_embed_model()
    texts = [
        f"{s['title'] or s['section']}\n\n{s['keywords'] or ''}".strip()
        for s in sections
    ]

    embeddings = embed_model.get_text_embedding_batch(texts, show_progress=True)
    vectors = np.array(embeddings, dtype=np.float32)

    ids = np.array([s["id"] for s in sections], dtype=np.uint64)
    meta = {
        str(s["id"]): {"file": s["file"], "section": s["section"], "tags": s["tags"] or ""}
        for s in sections
    }

    index = turbovec.IdMapIndex()
    index.add_with_ids(vectors, ids)
    index.prepare()

    _save_index(index, meta)

    return f"Indexed {len(sections)} sections → {cfg.vault_rag_tvim}"


def handle_query_vault(query: str, top_k: int = 8) -> str:
    """Semantic search over the vault. Returns top_k relevant chunks."""
    index, meta = _load_index()
    if index is None:
        return "Vault semantic index is empty. Run vault_rag__index_vault first."

    embed_model = _get_embed_model()
    q_vec = np.array([embed_model.get_text_embedding(query)], dtype=np.float32)
    hits = _rag_query(index, meta, q_vec, k=top_k)

    results = [
        f"### {h.get('file', 'unknown')} — {h.get('section', '')} (score: {h['score']:.3f})\n\n{h.get('file', '')}/{h.get('section', '')}"
        for h in hits
    ]
    return "\n\n---\n\n".join(results) if results else "No relevant chunks found."


def handle_fts_vault(query: str, limit: int = 10, folder: str = "") -> str:
    """Fast full-text keyword search over vault sections (no embeddings needed, always available).

    Args:
        query:  Keywords to search for.
        limit:  Max results to return (default 10).
        folder: Optional vault-relative folder prefix to restrict search
                (e.g. "Documentation/passive_learning_coding").
    """
    con = sqlite3.connect(str(cfg.vault_index_db))
    if folder:
        rows = con.execute(
            """
            SELECT s.file, s.section, snippet(sections_fts, 1, '[', ']', '...', 20) AS snippet
            FROM sections_fts
            JOIN sections s ON sections_fts.rowid = s.id
            WHERE sections_fts MATCH ? AND s.folder LIKE ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, f"{folder.rstrip('/')}%", limit),
        ).fetchall()
    else:
        rows = con.execute(
            """
            SELECT s.file, s.section, snippet(sections_fts, 1, '[', ']', '...', 20) AS snippet
            FROM sections_fts
            JOIN sections s ON sections_fts.rowid = s.id
            WHERE sections_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()
    con.close()

    if not rows:
        return f"No results for: {query}"

    return "\n\n".join(f"**{file}** — {section}\n{snip}" for file, section, snip in rows)


def handle_smart_search(query: str, fts_candidate_limit: int = 50, top_k: int = 5, folder: str = "") -> str:
    """Hybrid retrieval — FTS narrows candidates, TurboVec reranks semantically.

    Pipeline: FTS(query, limit=fts_candidate_limit) → allowlist IDs →
    TurboVec.search(allowlist=..., k=top_k) → ranked results.

    Falls back to FTS-only if semantic index is not built.
    Falls back to pure semantic if FTS returns no candidates.

    Args:
        query:               Keywords / natural-language query.
        fts_candidate_limit: Max FTS candidates passed to TurboVec reranker (default 50).
        top_k:               Final result count (default 5).
        folder:              Optional vault-relative folder prefix to restrict search
                             (e.g. "Documentation/passive_learning_coding").
    """
    # --- FTS: fetch candidate pool ---
    con = sqlite3.connect(str(cfg.vault_index_db))
    if folder:
        fts_rows = con.execute(
            """
            SELECT s.id, s.file, s.section, snippet(sections_fts, 1, '[', ']', '...', 20) AS snippet
            FROM sections_fts
            JOIN sections s ON sections_fts.rowid = s.id
            WHERE sections_fts MATCH ? AND s.folder LIKE ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, f"{folder.rstrip('/')}%", fts_candidate_limit),
        ).fetchall()
    else:
        fts_rows = con.execute(
            """
            SELECT s.id, s.file, s.section, snippet(sections_fts, 1, '[', ']', '...', 20) AS snippet
            FROM sections_fts
            JOIN sections s ON sections_fts.rowid = s.id
            WHERE sections_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, fts_candidate_limit),
        ).fetchall()
    con.close()

    fts_snippets = {row[0]: (row[1], row[2], row[3]) for row in fts_rows}

    index, meta = _load_index()

    # --- Fallback: no semantic index ---
    if index is None:
        lines = [f"**{file}** — {section}\n{snip}" for _, file, section, snip in fts_rows[:top_k]]
        return "\n\n".join(lines) if lines else f"No results found for: {query}"

    embed_model = _get_embed_model()
    q_vec = np.array([embed_model.get_text_embedding(query)], dtype=np.float32)

    # --- Hybrid: semantic rerank over FTS candidates ---
    if fts_snippets:
        allowlist = np.array(list(fts_snippets.keys()), dtype=np.uint64)
        scores, ids = index.search(q_vec, k=top_k, allowlist=allowlist)
    else:
        # No FTS hits — fall back to pure semantic across full index
        scores, ids = index.search(q_vec, k=top_k)

    results = []
    for score, doc_id in zip(scores[0], ids[0]):
        info = meta.get(str(doc_id), {})
        file = info.get("file", "unknown")
        section = info.get("section", "")
        snip = fts_snippets.get(doc_id, (None, None, ""))[2]
        entry = f"**{file}** — {section} (score: {score:.3f})"
        if snip:
            entry += f"\n{snip}"
        results.append(entry)

    return "\n\n".join(results) if results else f"No results found for: {query}"


def handle_index_status() -> str:
    """Check index status: TurboVec chunk count + SQLite section count."""
    index, _ = _load_index()
    tv_count = len(index) if index is not None else 0
    con = sqlite3.connect(str(cfg.vault_index_db))
    sqlite_count = con.execute("SELECT COUNT(*) FROM sections").fetchone()[0]
    con.close()
    status = "built" if tv_count > 0 else "not built — run vault_rag__index_vault"
    return (
        f"Semantic index (TurboVec): {tv_count} chunks — {status}\n"
        f"FTS index (SQLite): {sqlite_count} sections\n"
        f"Index path: {cfg.vault_rag_tvim}"
    )


def prune_file_sections(path: str) -> int:
    """Remove all TurboVec index entries for a vault-relative file path.

    Called by vault.handle_delete and handle_move to keep the index in sync.
    Returns the number of sections removed. Silently returns 0 if index not built.
    """
    index, meta = _load_index()
    if index is None:
        return 0

    con = sqlite3.connect(str(cfg.vault_index_db))
    rows = con.execute("SELECT id FROM sections WHERE file = ?", (path,)).fetchall()
    con.close()

    removed = 0
    for (section_id,) in rows:
        if index.remove(np.uint64(section_id)):
            meta.pop(str(section_id), None)
            removed += 1

    if removed:
        _save_index(index, meta)
    return removed


def handle_contains_section(section_id: int) -> str:
    """Check if a section ID is present in the TurboVec index."""
    index, meta = _load_index()
    if index is None:
        return "Index not built. Run vault_rag__index_vault first."
    present = index.contains(np.uint64(section_id))
    in_meta = str(section_id) in meta
    return (
        f"section_id={section_id}: vector={'present' if present else 'absent'}, "
        f"meta={'present' if in_meta else 'absent'}"
    )


def handle_index_file(path: str) -> str:
    """Incrementally index a single vault file into SQLite + TurboVec.

    Parses the file into sections, upserts them into the sections table and
    sections_fts, embeds each section, and adds to the live TurboVec index.
    Safe to call repeatedly — existing rows for this file are replaced.

    Args:
        path: vault-relative path, e.g. "Projects/My_Note.md"
    """
    norm = path if path.endswith(".md") else path + ".md"
    fp = cfg.vault_path / norm
    if not fp.exists():
        return f"File not found: {norm}"

    # Check skip folders
    parts = set(Path(norm).parts[:-1])
    if parts & _SKIP_FOLDERS:
        return f"Skipped — file is in a non-indexed folder: {norm}"

    text = fp.read_text(encoding="utf-8")
    sections = _parse_file_sections(norm, text)
    if not sections:
        return f"No indexable sections found in {norm}"

    con = sqlite3.connect(str(cfg.vault_index_db))

    # Remove old rows for this file
    old_ids = [r[0] for r in con.execute("SELECT id FROM sections WHERE file = ?", (norm,)).fetchall()]
    if old_ids:
        placeholders = ",".join("?" * len(old_ids))
        con.execute(f"DELETE FROM sections_fts WHERE rowid IN ({placeholders})", old_ids)
        con.execute(f"DELETE FROM sections WHERE id IN ({placeholders})", old_ids)

    # Insert new rows
    new_ids = []
    for s in sections:
        cur = con.execute(
            """INSERT INTO sections (file, folder, title, section, level, tags, keywords, created, updated, indexed_at)
               VALUES (:file, :folder, :title, :section, :level, :tags, :keywords, :created, :updated, :indexed_at)""",
            s,
        )
        new_id = cur.lastrowid
        new_ids.append(new_id)
        con.execute(
            "INSERT INTO sections_fts (rowid, section, tags, keywords, folder) VALUES (?, ?, ?, ?, ?)",
            (new_id, s["section"], s["tags"], s["keywords"], s["folder"]),
        )
    con.commit()
    con.close()

    # Embed and update TurboVec index
    index, meta = _load_index()
    if index is None:
        return f"SQLite updated ({len(new_ids)} sections). RAG index not built — run vault_rag__index_vault first."

    # Remove old vectors
    for old_id in old_ids:
        index.remove(np.uint64(old_id))
        meta.pop(str(old_id), None)

    embed_model = _get_embed_model()
    texts = [
        f"{s['title'] or s['section']}\n\n{s['keywords'] or ''}".strip()
        for s in sections
    ]
    embeddings = embed_model.get_text_embedding_batch(texts, show_progress=False)
    vectors = np.array(embeddings, dtype=np.float32)
    ids = np.array(new_ids, dtype=np.uint64)

    index.add_with_ids(vectors, ids)
    index.prepare()

    for section, new_id in zip(sections, new_ids):
        meta[str(new_id)] = {"file": section["file"], "section": section["section"], "tags": section["tags"]}

    _save_index(index, meta)
    return f"Indexed {len(new_ids)} sections from {norm} (replaced {len(old_ids)} old)."


def handle_unindexed_files(folder: str = "") -> dict:
    """Find vault .md files not yet present in the RAG index (vault_index.sqlite).

    Diffs the vault filesystem against the sections table. Returns files that
    exist on disk but have no indexed sections — these need handle_index_file called on them.

    Args:
        folder: Optional vault-relative subfolder to scope the scan (e.g. "TaskContexts").
                Defaults to entire vault.

    Returns:
        {"unindexed": [...], "total_on_disk": N, "total_indexed_files": M}
    """
    scan_root = cfg.vault_path / folder if folder else cfg.vault_path

    # All .md files on disk (vault-relative paths, skip hidden/Obsidian dirs)
    on_disk: set[str] = set()
    for fp in scan_root.rglob("*.md"):
        parts = set(fp.relative_to(cfg.vault_path).parts[:-1])
        if parts & _SKIP_FOLDERS:
            continue
        on_disk.add(str(fp.relative_to(cfg.vault_path)))

    # Files that have at least one row in sections
    con = sqlite3.connect(str(cfg.vault_index_db))
    indexed_files: set[str] = {
        row[0] for row in con.execute("SELECT DISTINCT file FROM sections").fetchall()
    }
    con.close()

    # Scope indexed set to folder if specified
    if folder:
        prefix = folder.rstrip("/") + "/"
        indexed_files = {f for f in indexed_files if f.startswith(prefix)}

    unindexed = sorted(on_disk - indexed_files)
    return {
        "unindexed": unindexed,
        "total_on_disk": len(on_disk),
        "total_indexed_files": len(indexed_files),
    }


def handle_remove_section(section_id: int) -> str:
    """Remove a single section from the TurboVec index by its SQLite section ID.

    Useful for pruning deleted or stale vault sections without a full rebuild.
    Updates both the .tvim index and .meta.json sidecar atomically.
    """
    index, meta = _load_index()
    if index is None:
        return "Index not built. Run vault_rag__index_vault first."

    uid = np.uint64(section_id)
    removed = index.remove(uid)
    if not removed:
        return f"section_id={section_id} not found in index."

    meta.pop(str(section_id), None)
    _save_index(index, meta)
    return f"Removed section_id={section_id}. Index now has {len(index)} chunks."
