#!/usr/bin/env python3
"""
index_vault_sections.py — Build a SQLite index of vault note sections.

Walks all .md files in VAULT_PATH, extracts frontmatter tags + substantive
section headings (## and ###), skips boilerplate sections. Writes to
vault_index.sqlite in the vault root.

Usage:
    uv run python tools/index_vault_sections.py
    uv run python tools/index_vault_sections.py --vault /path/to/vault
    uv run python tools/index_vault_sections.py --stats
"""

import argparse
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from config import config as settings

VAULT_PATH = Path(os.environ.get("VAULT_PATH", settings.vault_path))
DB_PATH = settings.vault_index_db

# Section headings to skip — boilerplate, not content
SKIP_HEADINGS = {
    "contents", "related", "summary", "sources", "notes", "index",
    "overview", "introduction", "references", "see also", "links",
    "navigation", "tags", "metadata", "index terms",
}

# Folders to skip entirely — Daily/Weekly/Monthly are time-series reports, not reference content
SKIP_FOLDERS = {".obsidian", "Tmp", ".git", "Cache", "Daily", "Weekly", "Monthly"}


def is_boilerplate(heading: str) -> bool:
    return heading.strip().lower() in SKIP_HEADINGS


def parse_frontmatter(text: str) -> dict:
    """Extract title, tags, created, updated from YAML frontmatter."""
    result = {"title": None, "tags": [], "created": None, "updated": None}
    if not text.startswith("---"):
        return result
    end = text.find("\n---", 3)
    if end == -1:
        return result
    fm = text[3:end]

    # title
    m = re.search(r"^title:\s*(.+)$", fm, re.MULTILINE)
    if m:
        result["title"] = m.group(1).strip().strip('"')

    # created / updated
    for field in ("created", "updated"):
        m = re.search(rf"^{field}:\s*(.+)$", fm, re.MULTILINE)
        if m:
            result[field] = m.group(1).strip()

    # tags — handle both inline list and block list
    m = re.search(r"^tags:\s*\[(.+?)\]", fm, re.MULTILINE)
    if m:
        result["tags"] = [t.strip().strip('"') for t in m.group(1).split(",")]
    else:
        # block list
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


STOPWORDS = {
    "the", "and", "for", "that", "this", "with", "from", "have", "will",
    "been", "are", "was", "were", "not", "but", "into", "also", "than",
    "then", "when", "each", "more", "some", "such", "their", "there",
    "these", "they", "what", "which", "your", "can", "may", "per",
    "all", "any", "its", "our", "you", "has", "had", "use",
}


def extract_keywords(body: str, max_keywords: int = 30) -> str:
    """Extract significant keywords from section body text."""
    # Strip markdown: code blocks, URLs, wikilinks, table pipes, punctuation
    body = re.sub(r"```.*?```", " ", body, flags=re.DOTALL)
    body = re.sub(r"`[^`]+`", " ", body)
    body = re.sub(r"https?://\S+", " ", body)
    body = re.sub(r"\[\[([^\]|#]+)[^\]]*\]\]", r"\1", body)  # keep wikilink text
    # Capture inline #hashtags before stripping punctuation (e.g. tags: #indipop #90s)
    inline_tags = re.findall(r"#([a-zA-Z][a-zA-Z0-9_-]*)", body)
    # Whitelist short domain tokens before punctuation stripping:
    #   D1–D60  — divisional charts (D9, D12, D10 ...)
    #   H1–H12  — house notation (H4, H10 ...)
    #   AD, MD  — antardasha / mahadasha abbreviations
    short_tokens = re.findall(r"\b(D\d{1,2}|H\d{1,2}|AD|MD)\b", body)
    # Preserve hyphenated tokens like DNS-01, HTTP-01, Let's-Encrypt as single keywords
    hyphen_tokens = re.findall(r"\b([a-zA-Z][a-zA-Z0-9]*-\d+[a-zA-Z0-9]*)\b", body)
    body = re.sub(r"[|#*_~>\-]", " ", body)
    body = re.sub(r"[^\w\s/]", " ", body)

    seen: dict[str, int] = {}
    # Boost inline hashtags so they always make the keyword list
    for tag in inline_tags:
        tok = tag.lower()
        if len(tok) >= 2:
            seen[tok] = seen.get(tok, 0) + 5
    # Boost whitelisted short tokens so they always make the keyword list
    for tok in short_tokens:
        tok = tok.lower()
        seen[tok] = seen.get(tok, 0) + 5
    # Boost hyphenated tokens (e.g. dns-01, http-01) and also store without hyphen for FTS
    for tok in hyphen_tokens:
        tok_lower = tok.lower()
        seen[tok_lower] = seen.get(tok_lower, 0) + 5
        tok_nohyphen = tok_lower.replace("-", "")
        seen[tok_nohyphen] = seen.get(tok_nohyphen, 0) + 5
    for word in body.lower().split():
        word = word.strip("/")
        if len(word) >= 3 and word not in STOPWORDS and not word.isdigit():
            seen[word] = seen.get(word, 0) + 1

    # Sort by frequency, take top max_keywords
    ranked = sorted(seen, key=lambda w: -seen[w])[:max_keywords]
    return ",".join(ranked)


INDEX_TERMS_HEADING = "index terms"


def extract_index_terms(text: str) -> str:
    """Extract raw text from the '### Index Terms' section, if present.

    Returns a comma-joined string of tokens for keyword injection into all
    other section rows. The Index Terms section itself is never inserted as
    a section row — it exists only to boost searchability of buried fields
    (janma nakshatra, lagna, atmakaraka, birth date, etc.).
    """
    m = re.search(r"^#{2,3}\s+Index Terms\s*\n(.*?)(?=^#{1,3}\s|\Z)", text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    if not m:
        return ""
    # Normalise separators (|, newlines, commas) into a flat token list
    raw = m.group(1)
    tokens = re.split(r"[|\n,]+", raw)
    # Strip key:value colon pairs — keep both key and value as tokens
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


def extract_sections(text: str) -> list[tuple[str, int, str]]:
    """Return list of (heading_text, level, keywords) for ## and ### only.

    The special '### Index Terms' section is excluded from results — its
    contents are extracted separately via extract_index_terms() and injected
    into every other section row's keywords by build_index().
    """
    lines = text.splitlines()
    heading_positions = []
    for i, line in enumerate(lines):
        m = re.match(r"^(#{2,3})\s+(.+)$", line)
        if m:
            level = len(m.group(1))
            heading = m.group(2).strip()
            if not is_boilerplate(heading) and heading.lower() != INDEX_TERMS_HEADING:
                heading_positions.append((i, heading, level))

    sections = []
    for idx, (line_no, heading, level) in enumerate(heading_positions):
        next_line = heading_positions[idx + 1][0] if idx + 1 < len(heading_positions) else len(lines)
        body = "\n".join(lines[line_no + 1:next_line])
        keywords = extract_keywords(body)
        sections.append((heading, level, keywords))
    return sections


def infer_folder_tags(folder: str, path_segments: list[str], folder_sections: list[dict]) -> str:
    """Derive tags for a folder from its path segments + content tags/keywords.

    path_segments   — parts of the folder path (already split)
    folder_sections — list of dicts with 'tags' and 'keywords' keys from sections in this folder
    Returns a comma-joined tag string, deduplicated, lowercase.
    """
    tag_freq: dict[str, int] = {}

    # Path segments as tags (lowercased, spaces→underscore)
    for seg in path_segments:
        if seg == ".":
            continue
        tok = seg.lower().replace(" ", "_").replace("-", "_")
        tag_freq[tok] = tag_freq.get(tok, 0) + 10  # boost path tags

    # Collect tags and keywords from all sections in this folder
    for row in folder_sections:
        for field in ("tags", "keywords"):
            val = row.get(field) or ""
            for tok in val.split(","):
                tok = tok.strip().lower().replace(" ", "_").replace("-", "_")
                if tok and len(tok) >= 3 and tok not in STOPWORDS:
                    tag_freq[tok] = tag_freq.get(tok, 0) + 1

    # Top 20 by frequency
    top = sorted(tag_freq, key=lambda t: -tag_freq[t])[:20]
    return ",".join(top)


def build_index(vault: Path, db: Path) -> tuple[int, int]:
    """Walk vault, index sections. Returns (files_indexed, sections_indexed)."""
    conn = sqlite3.connect(db)
    cur = conn.cursor()

    cur.executescript("""
        DROP TABLE IF EXISTS sections_fts;
        DROP TABLE IF EXISTS sections;
        CREATE TABLE sections (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            file        TEXT NOT NULL,
            folder      TEXT NOT NULL,
            title       TEXT,
            section     TEXT NOT NULL,
            level       INTEGER NOT NULL,
            tags        TEXT,
            keywords    TEXT,
            created     TEXT,
            updated     TEXT,
            indexed_at  TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_file   ON sections(file);
        CREATE INDEX IF NOT EXISTS idx_folder ON sections(folder);

        CREATE VIRTUAL TABLE sections_fts USING fts5(
            section,
            tags,
            keywords,
            folder,
            content='sections',
            content_rowid='id',
            tokenize='unicode61 remove_diacritics 1'
        );

        DROP TABLE IF EXISTS folders;
        CREATE TABLE folders (
            folder      TEXT PRIMARY KEY,
            folder_tags TEXT,
            indexed_at  TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS folders_fts USING fts5(
            folder,
            folder_tags,
            content='folders',
            content_rowid='rowid',
            tokenize='unicode61 remove_diacritics 1'
        );

        DROP TABLE IF EXISTS tags;
        CREATE TABLE tags (
            tag         TEXT PRIMARY KEY,
            count       INTEGER NOT NULL,
            files       TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS tags_fts USING fts5(
            tag,
            content='tags',
            content_rowid='rowid',
            tokenize='unicode61 remove_diacritics 1'
        );

        DROP TABLE IF EXISTS files;
        CREATE TABLE files (
            file        TEXT PRIMARY KEY,
            stem        TEXT NOT NULL,
            folder      TEXT NOT NULL,
            indexed_at  TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_files_stem   ON files(stem);
        CREATE INDEX IF NOT EXISTS idx_files_folder ON files(folder);
    """)

    # vault_keyword_hints persists across rebuilds — no DROP
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vault_keyword_hints (
            keyword       TEXT PRIMARY KEY,
            count         INTEGER NOT NULL DEFAULT 1,
            last_searched TEXT NOT NULL,
            top_file      TEXT,           -- file most often returned for this keyword
            domain        TEXT            -- inferred domain (e.g. astrology, philosophy, vault)
        )
    """)
    # Migrate existing rows that predate the new columns
    for col in ("top_file", "domain"):
        try:
            cur.execute(f"ALTER TABLE vault_keyword_hints ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass  # column already exists

    now = datetime.now().isoformat(timespec="seconds")
    files_done = 0
    sections_done = 0
    # folder → list of {tags, keywords} for folder tag inference
    folder_data: dict[str, list[dict]] = {}
    # tag → set of files
    tag_files: dict[str, set[str]] = {}

    for md in sorted(vault.rglob("*.md")):
        # Skip unwanted folders
        parts = md.relative_to(vault).parts
        if any(p in SKIP_FOLDERS for p in parts):
            continue

        rel = str(md.relative_to(vault))
        folder = str(md.relative_to(vault).parent)

        # Register every .md file in the files table for fast filename search
        cur.execute(
            "INSERT OR REPLACE INTO files (file, stem, folder, indexed_at) VALUES (?, ?, ?, ?)",
            (rel, md.stem, folder, now),
        )

        text = md.read_text(encoding="utf-8", errors="ignore")
        fm = parse_frontmatter(text)
        sections = extract_sections(text)

        if not sections:
            continue
        tags_str = ",".join(fm["tags"]) if fm["tags"] else None
        index_terms = extract_index_terms(text)  # extra keywords to inject into every row

        # Collect all tags for this file: frontmatter + inline #hashtags
        file_tags: set[str] = set(t.lower() for t in fm["tags"])
        for inline_tag in re.findall(r"#([a-zA-Z][a-zA-Z0-9_-]*)", text):
            file_tags.add(inline_tag.lower())
        for t in file_tags:
            tag_files.setdefault(t, set()).add(rel)

        for heading, level, keywords in sections:
            # Merge section keywords with file-level index terms
            merged = ",".join(filter(None, [keywords, index_terms])) or None
            cur.execute(
                """INSERT INTO sections
                   (file, folder, title, section, level, tags, keywords, created, updated, indexed_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (rel, folder, fm["title"], heading, level,
                 tags_str, merged, fm["created"], fm["updated"], now),
            )
            sections_done += 1
            folder_data.setdefault(folder, []).append({"tags": tags_str, "keywords": merged})

        files_done += 1

    # Build folders table
    for folder, rows in folder_data.items():
        segments = list(Path(folder).parts)
        ftags = infer_folder_tags(folder, segments, rows)
        cur.execute(
            "INSERT OR REPLACE INTO folders (folder, folder_tags, indexed_at) VALUES (?, ?, ?)",
            (folder, ftags, now),
        )

    # Build tags table
    for tag, files in sorted(tag_files.items()):
        cur.execute(
            "INSERT OR REPLACE INTO tags (tag, count, files) VALUES (?, ?, ?)",
            (tag, len(files), ",".join(sorted(files))),
        )

    # Populate FTS indexes
    cur.executescript("""
        INSERT INTO sections_fts(rowid, section, tags, keywords, folder)
            SELECT id, section, COALESCE(tags,''), COALESCE(keywords,''), folder FROM sections;

        INSERT INTO folders_fts(rowid, folder, folder_tags)
            SELECT rowid, folder, COALESCE(folder_tags,'') FROM folders;

        INSERT INTO tags_fts(rowid, tag)
            SELECT rowid, tag FROM tags;
    """)

    conn.commit()
    conn.close()
    return files_done, sections_done


def update_index(vault: Path, db: Path) -> tuple[int, int]:
    """Incremental update — add only files not yet in the files table.

    Skips a full DROP+recreate. Useful after adding new notes without
    waiting for a full rebuild. Falls back to build_index if db missing.
    """
    if not db.exists():
        print("Index not found — running full build.")
        return build_index(vault, db)

    conn = sqlite3.connect(db)
    cur = conn.cursor()

    # Files already indexed
    cur.execute("SELECT file FROM files")
    indexed = {row[0] for row in cur.fetchall()}

    now = datetime.now().isoformat(timespec="seconds")
    files_done = 0
    sections_done = 0

    for md in sorted(vault.rglob("*.md")):
        parts = md.relative_to(vault).parts
        if any(p in SKIP_FOLDERS for p in parts):
            continue

        rel = str(md.relative_to(vault))
        if rel in indexed:
            continue  # already in index — skip

        folder = str(md.relative_to(vault).parent)

        # Register in files table
        cur.execute(
            "INSERT OR REPLACE INTO files (file, stem, folder, indexed_at) VALUES (?, ?, ?, ?)",
            (rel, md.stem, folder, now),
        )

        text = md.read_text(encoding="utf-8", errors="ignore")
        fm = parse_frontmatter(text)
        sections = extract_sections(text)
        tags_str = ",".join(fm["tags"]) if fm["tags"] else None
        index_terms = extract_index_terms(text)

        for heading, level, keywords in sections:
            merged = ",".join(filter(None, [keywords, index_terms])) or None
            cur.execute(
                """INSERT INTO sections
                   (file, folder, title, section, level, tags, keywords, created, updated, indexed_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (rel, folder, fm["title"], heading, level,
                 tags_str, merged, fm["created"], fm["updated"], now),
            )
            rowid = cur.lastrowid
            cur.execute(
                "INSERT INTO sections_fts(rowid, section, tags, keywords, folder) VALUES (?, ?, ?, ?, ?)",
                (rowid, heading, tags_str or "", merged or "", folder),
            )
            sections_done += 1

        files_done += 1
        print(f"  + {rel}")

    conn.commit()
    conn.close()
    return files_done, sections_done


def print_stats(db: Path):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sections")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT file) FROM sections")
    files = cur.fetchone()[0]
    cur.execute("SELECT folder, COUNT(*) as n FROM sections GROUP BY folder ORDER BY n DESC LIMIT 10")
    rows = cur.fetchall()
    cur.execute("SELECT folder, folder_tags FROM folders ORDER BY folder LIMIT 20")
    ftag_rows = cur.fetchall()
    conn.close()

    print(f"Total sections : {total}")
    print(f"Files indexed  : {files}")
    print(f"\nTop folders:")
    for folder, n in rows:
        print(f"  {folder:<45} {n}")
    print(f"\nFolder tags (sample):")
    for folder, ftags in ftag_rows:
        print(f"  {folder:<45} {ftags}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", default=str(VAULT_PATH))
    parser.add_argument("--update", action="store_true",
                        help="Incremental update — add new files only, skip full rebuild")
    parser.add_argument("--stats", action="store_true", help="Show stats after indexing")
    args = parser.parse_args()

    vault = Path(args.vault)
    db = settings.vault_index_db

    if args.update:
        print(f"Updating index (new files only): {vault}")
        files, sections = update_index(vault, db)
        print(f"Done — {files} new files, {sections} new sections → {db}")
    else:
        print(f"Indexing vault (full rebuild): {vault}")
        files, sections = build_index(vault, db)
        print(f"Done — {files} files, {sections} sections → {db}")

    if args.stats:
        print()
        print_stats(db)
