# Search architecture and schema documented in vault:
# Documentation/Tools/VAULT_SECTION_INDEX.md
import re
import sqlite3
from datetime import date
from pathlib import Path

from config import config as cfg

VAULT_NAME          = cfg.vault_name
VAULT_PATH          = cfg.vault_path
VAULT_INDEX_DB      = cfg.vault_index_db
TABLE_KEYWORD_HINTS = cfg.table_keyword_hints


def _vault_path(path: str) -> Path:
    p = path if path.endswith(".md") else path + ".md"
    return VAULT_PATH / p


def _strip_code_blocks(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_block = text[3:end].strip()
    body = text[end + 4:]
    meta: dict = {}
    for line in fm_block.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    return meta, body


def handle_read(path: str) -> str:
    """Read a note from the vault."""
    fp = _vault_path(path)
    if not fp.exists():
        raise FileNotFoundError(f"Note not found: {path}")
    return fp.read_text()


def handle_write(path: str, content: str) -> str:
    """Create or overwrite a vault note."""
    fp = _vault_path(path)
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content)
    return f"✓ Written: {path}"


def handle_append(path: str, content: str) -> str:
    """Append content to an existing vault note."""
    fp = _vault_path(path)
    if not fp.exists():
        raise FileNotFoundError(f"Note not found: {path}")
    fp.write_text(fp.read_text() + "\n" + content)
    return f"✓ Appended to: {path}"


def handle_delete(path: str) -> str:
    """Delete a vault note."""
    fp = _vault_path(path)
    if not fp.exists():
        raise FileNotFoundError(f"Note not found: {path}")
    fp.unlink()
    from tools.vault_rag import prune_file_sections
    norm = str(fp.relative_to(VAULT_PATH))
    pruned = prune_file_sections(norm)
    suffix = f" ({pruned} RAG sections pruned)" if pruned else ""
    return f"✓ Deleted: {path}{suffix}"


def handle_move(path: str, to: str) -> str:
    """Move or rename a vault note."""
    src = _vault_path(path)
    dst = _vault_path(to)
    if not src.exists():
        raise FileNotFoundError(f"Note not found: {path}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)
    from tools.vault_rag import prune_file_sections
    norm = str(src.relative_to(VAULT_PATH))
    pruned = prune_file_sections(norm)
    suffix = f" ({pruned} RAG sections pruned — re-index to add new path)" if pruned else ""
    return f"✓ Moved: {path} → {to}{suffix}"


def handle_list(path: str = "") -> str:
    """List .md files in the vault or a specific folder."""
    files = sorted(str(f.relative_to(VAULT_PATH)) for f in VAULT_PATH.rglob("*.md")
                   if not any(p.startswith(".") for p in f.parts))
    return "\n".join(f for f in files if not path or f.startswith(path))



def handle_vault_keyword_hints(limit: int = 20) -> str:
    """Show frequently searched keywords ranked by search count."""
    db = VAULT_INDEX_DB
    if not db.exists():
        return "Index not found."
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute(
            f"SELECT keyword, count, last_searched, top_file, domain FROM {TABLE_KEYWORD_HINTS} ORDER BY count DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        conn.close()
    except sqlite3.OperationalError:
        return f"{TABLE_KEYWORD_HINTS} table not found. Run: uv run python tools/index_vault_sections.py"

    if not rows:
        return "No searches logged yet."

    lines = [f"Top {len(rows)} searched keywords:\n"]
    for keyword, count, last, top_file, domain in rows:
        domain_str = f"[{domain}]" if domain else ""
        file_str = f" → {top_file}" if top_file else ""
        lines.append(f"  {count:>4}×  {keyword:<25} {domain_str:<16}{file_str}  (last: {last})")
    return "\n".join(lines)


def handle_links(path: str) -> str:
    """List all outgoing [[wikilinks]] from a vault note."""
    fp = _vault_path(path)
    text = _strip_code_blocks(fp.read_text(errors="ignore"))
    links = re.findall(r"\[\[([^\]|#]+)", text)
    return "\n".join(sorted(set(links))) if links else "No outgoing links."


def handle_backlinks(path: str) -> str:
    """Find all notes that link to a given vault note."""
    target = re.escape(Path(path).stem)
    pattern = re.compile(r"\[\[" + target + r"[\]|#]", re.IGNORECASE)
    matches = []
    for fp in VAULT_PATH.rglob("*.md"):
        if any(p.startswith(".") for p in fp.parts):
            continue
        text = _strip_code_blocks(fp.read_text(errors="ignore"))
        if pattern.search(text):
            matches.append(str(fp.relative_to(VAULT_PATH)))
    return "\n".join(sorted(matches)) if matches else "No backlinks found."


def handle_daily_read() -> str:
    """Read today's daily summary note (Daily/YYYY-MM-DD_summary.md)."""
    today = date.today().strftime("%Y-%m-%d")
    fp = VAULT_PATH / "Daily" / f"{today}_summary.md"
    return fp.read_text() if fp.exists() else f"No daily summary for {today}."


def handle_outline(path: str) -> str:
    """Show the heading tree for a vault note."""
    fp = _vault_path(path)
    text = _strip_code_blocks(fp.read_text(errors="ignore"))
    headings = [l.rstrip() for l in text.splitlines() if l.startswith("#")]
    return "\n".join(headings) if headings else "No headings found."


def handle_tags(path: str = "") -> str:
    """List tags in the vault or for a specific note."""
    counts: dict[str, int] = {}
    files_to_scan = [_vault_path(path)] if path else list(VAULT_PATH.rglob("*.md"))
    inline_re = re.compile(r"^tags:\s*\[([^\]]+)\]", re.MULTILINE)
    block_re = re.compile(r"^tags:\s*\n((?:\s*-\s*.+\n?)+)", re.MULTILINE)
    item_re = re.compile(r"-\s*(.+)")
    hashtag_re = re.compile(r"(?<!\[)#([\w/]+)")
    for fp in files_to_scan:
        if not fp.exists():
            continue
        text = fp.read_text(errors="ignore")
        meta, body = _parse_frontmatter(text)
        tags: list[str] = []
        fm_slice = text[:text.find("\n---", 3) + 4] if text.startswith("---") else ""
        for m in inline_re.finditer(fm_slice):
            tags += [t.strip() for t in m.group(1).split(",")]
        for m in block_re.finditer(fm_slice):
            tags += [item_re.search(l).group(1).strip() for l in m.group(1).splitlines() if item_re.search(l)]
        tags += hashtag_re.findall(_strip_code_blocks(body))
        for tag in tags:
            tag = tag.strip()
            if tag:
                counts[tag] = counts.get(tag, 0) + 1
    return "\n".join(f"{t}: {c}" for t, c in sorted(counts.items(), key=lambda x: -x[1]))


def handle_tasks(scope: str = "all") -> str:
    """List incomplete tasks. scope: 'all', 'daily', or a note path."""
    task_re = re.compile(r"- \[ \] (.+)")
    results = []
    if scope == "daily":
        today = date.today().strftime("%Y-%m-%d")
        files = [VAULT_PATH / "Daily" / f"{today}_summary.md"]
    elif scope == "all":
        files = [f for f in VAULT_PATH.rglob("*.md") if not any(p.startswith(".") for p in f.parts)]
    else:
        files = [_vault_path(scope)]
    for fp in files:
        if not fp.exists():
            continue
        for m in task_re.finditer(fp.read_text(errors="ignore")):
            results.append(f"[{fp.relative_to(VAULT_PATH)}] {m.group(1)}")
    return "\n".join(results) if results else "No incomplete tasks found."


def handle_stats() -> str:
    """Get total note count for the vault."""
    all_files = [f for f in VAULT_PATH.rglob("*.md") if not any(p.startswith(".") for p in f.parts)]
    return f"Vault: {VAULT_NAME}\nTotal notes: {len(all_files)}"


def _vault_db() -> sqlite3.Connection | None:
    db = VAULT_INDEX_DB
    return sqlite3.connect(db) if db.exists() else None


def _fts_query(terms: str) -> str:
    """Convert a plain search string to an FTS5 query.

    Wraps each whitespace-separated token in double-quotes so special chars
    are treated literally, then joins with AND so all terms must match.
    """
    tokens = terms.strip().split()
    return " AND ".join(f'"{t}"' for t in tokens) if tokens else '""'


def handle_section_search(query: str, tag: str = "", folder: str = "", limit: int = 20) -> str:
    """Search vault section headings by keyword, frontmatter tag, or folder path.

    Uses the pre-built FTS5 section index (vault_index.sqlite).
    Run tools/index_vault_sections.py to rebuild the index after adding notes.

    Args:
        query:  Keyword to match against section headings / keywords (FTS5). Pass "" to list all.
        tag:    Filter by frontmatter tag (FTS5 match against tags column).
        folder: Filter by vault folder path (partial LIKE match).
        limit:  Max results to return (default 20).
    """
    conn = _vault_db()
    if not conn:
        return "Section index not found. Run: uv run python tools/index_vault_sections.py"

    cur = conn.cursor()

    # Build FTS5 column filters — query hits section+keywords, tag hits tags column
    fts_parts = []
    if query:
        fts_parts.append(f"{{section keywords}} : {_fts_query(query)}")
    if tag:
        fts_parts.append(f"{{tags}} : {_fts_query(tag)}")

    try:
        if fts_parts:
            fts_expr = " AND ".join(fts_parts)
            if folder:
                cur.execute(
                    """SELECT s.file, s.section, s.level
                       FROM sections_fts f
                       JOIN sections s ON s.id = f.rowid
                       WHERE sections_fts MATCH ?
                         AND LOWER(s.folder) LIKE LOWER(?)
                       ORDER BY rank, s.file, s.id LIMIT ?""",
                    (fts_expr, f"%{folder}%", limit),
                )
            else:
                cur.execute(
                    """SELECT s.file, s.section, s.level
                       FROM sections_fts f
                       JOIN sections s ON s.id = f.rowid
                       WHERE sections_fts MATCH ?
                       ORDER BY rank, s.file, s.id LIMIT ?""",
                    (fts_expr, limit),
                )
        elif folder:
            cur.execute(
                """SELECT file, section, level FROM sections
                   WHERE LOWER(folder) LIKE LOWER(?) ORDER BY file, id LIMIT ?""",
                (f"%{folder}%", limit),
            )
        else:
            cur.execute("SELECT file, section, level FROM sections ORDER BY file, id LIMIT ?", (limit,))

        rows = cur.fetchall()
    except sqlite3.OperationalError as e:
        conn.close()
        return f"Search error (try rebuilding index): {e}"

    conn.close()

    if not rows:
        return "No matching sections found."

    lines = []
    current_file = None
    for file, section, level in rows:
        if file != current_file:
            lines.append(f"\n{file}")
            current_file = file
        indent = "  " if level == 3 else ""
        lines.append(f"  {indent}{'###' if level == 3 else '##'} {section}")
    lines.append(f"\n({len(rows)} results)")
    return "\n".join(lines).strip()


def handle_tags_search(query: str = "", limit: int = 30) -> str:
    """List vault tags with file counts, optionally filtered by partial name.

    Args:
        query: Partial tag name to filter (e.g. "raga", "indipop"). Pass "" to list all tags.
        limit: Max tags to return, sorted by count descending (default 30).
    """
    conn = _vault_db()
    if not conn:
        return "Section index not found. Run: uv run python tools/index_vault_sections.py"

    cur = conn.cursor()
    if query:
        try:
            cur.execute(
                """SELECT t.tag, t.count FROM tags_fts f
                   JOIN tags t ON t.rowid = f.rowid
                   WHERE tags_fts MATCH ? ORDER BY t.count DESC LIMIT ?""",
                (_fts_query(query), limit),
            )
        except sqlite3.OperationalError:
            cur.execute(
                "SELECT tag, count FROM tags WHERE LOWER(tag) LIKE LOWER(?) ORDER BY count DESC LIMIT ?",
                (f"%{query}%", limit),
            )
    else:
        cur.execute("SELECT tag, count FROM tags ORDER BY count DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        suffix = f' matching "{query}"' if query else ""
        return f"No tags found{suffix}."

    query_suffix = f' matching "{query}"' if query else ""
    lines = [f"Tags{query_suffix} ({len(rows)} shown):\n"]
    for tag, count in rows:
        lines.append(f"  #{tag} — {count} {'file' if count == 1 else 'files'}")
    return "\n".join(lines)


def handle_filename_search(query: str, folder: str = "") -> str:
    """Search vault file names (stems) for a keyword — fast, no file reads.

    Args:
        query:  Keyword to match against the file name (case-insensitive).
        folder: Optional subfolder to restrict search (e.g. "Astrology").
    """
    query_lower = query.lower()
    search_root = VAULT_PATH / folder if folder else VAULT_PATH
    matches = [
        str(fp.relative_to(VAULT_PATH))
        for fp in sorted(search_root.rglob("*.md"))
        if not any(p.startswith(".") for p in fp.parts)
        and query_lower in fp.stem.lower()
    ]
    if not matches:
        return f"No files found with '{query}' in name."
    return "\n".join(matches) + f"\n\n({len(matches)} file{'s' if len(matches) != 1 else ''} found)"


def handle_folder_search(tag: str, limit: int = 20) -> str:
    """Find vault folders by inferred content tag.

    Searches the folders index — tags derived from path segments and the
    predominant topics found in files within each folder.

    Args:
        tag:   Topic tag to search for (partial match, e.g. "astrology", "market_intel").
        limit: Max folders to return (default 20).
    """
    conn = _vault_db()
    if not conn:
        return "Section index not found. Run: uv run python tools/index_vault_sections.py"

    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT f.folder, f.folder_tags FROM folders_fts ff
               JOIN folders f ON f.rowid = ff.rowid
               WHERE folders_fts MATCH ? ORDER BY f.folder LIMIT ?""",
            (_fts_query(tag), limit),
        )
    except sqlite3.OperationalError:
        cur.execute(
            "SELECT folder, folder_tags FROM folders WHERE LOWER(folder_tags) LIKE LOWER(?) ORDER BY folder LIMIT ?",
            (f"%{tag}%", limit),
        )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return f"No folders found matching tag '{tag}'."

    lines = [f"Folders matching '{tag}':\n"]
    for folder, folder_tags in rows:
        lines.append(f"  {folder}")
        lines.append(f"    tags: {folder_tags}\n")
    return "\n".join(lines).strip()
