# local-mac-summarize-claude-session

Automatically capture Claude Code session summaries to your Obsidian Daily notes.

## Overview

After each Claude Code session, use this skill to document:
- What you worked on
- How Claude solved problems
- What was created or changed
- Key insights and learnings
- Next steps and implications

All summaries are saved to `~/Documents/claude_documents/Daily/` with today's date.

## Usage

```bash
/local-mac-summarize-claude-session "# Daily Session\n\nContent..."
```

Or call the script directly:

```bash
~/workspace/claude_for_mac_local/tools/obsidian_summarize_session.sh "Session summary"
```

## Example

```bash
/local-mac-summarize-claude-session "# Daily Session: 2026-03-31

## 🎯 Session Goal
Consolidate all project wikis into Obsidian vault.

## 💭 Claude's Thinking
- Problem: Knowledge scattered across 3 wikis
- Solution: Centralize in [[claude-mac-obsidian]] vault
- Implementation: Migrate + create cross-links

## ✅ Accomplished
- Migrated 71 wiki files
- Created 8 project overviews
- Built 5 navigation guides
- Established 50+ cross-links
- Deleted redundant originals

## 💡 Key Insights
- Consolidated vault > scattered repos
- [[Bidirectional links]] enable discovery
- [[Knowledge graph]] connects all work

## 🚀 Next Steps
- Open vault in Obsidian
- Explore [[graph view]]
- Add daily journal entries"
```

## Output

Creates a dated file:
```
~/Documents/claude_documents/Daily/2026-03-31.md
```

The file is:
- ✅ In Obsidian vault (syncs to graph)
- ✅ Fully formatted markdown
- ✅ Searchable in Obsidian
- ✅ Linked to projects via [[references]]

## Integration

### With Obsidian
- All daily notes visible in Daily folder
- Full-text search across sessions
- Graph view shows session relationships
- Backlinks connect insights to projects

### With Projects
Use [[project-names]] in summaries to:
- Link session work to specific projects
- See what happened in each project timeline
- Discover cross-project connections
- Build context for future work

### With [[claude-mac-obsidian]]
Daily summaries are stored in your Obsidian vault, making them:
- Readable via `/claude-mac-obsidian read`
- Linkable from other notes
- Part of your knowledge graph
- Accessible from Claude future sessions

## Benefits

### For Reflection
Review past sessions to understand:
- How problems were solved
- What strategies worked
- Patterns in your thinking
- Progress over time

### For Continuity
Future sessions can quickly understand:
- What was accomplished
- Why decisions were made
- Ongoing context and goals
- Follow-up actions needed

### For Knowledge Building
Session notes create a searchable archive of:
- Insights and learnings
- Projects worked on
- Problems solved
- Ideas explored

## Best Practices

1. **Be Specific** — Include concrete details, not just "worked on X"
2. **Record Thinking** — Explain why decisions were made
3. **Use Headers** — Makes notes scannable later
4. **Add Links** — Use [[Project Name]] to connect to work
5. **Note Implications** — What became possible? What changed?
6. **Timestamp Key Moments** — When did major decisions happen?

## Example Structure

```markdown
# Daily Session: 2026-03-31

## 🎯 Session Goal
One-line objective

## 💭 Claude's Thinking
- Problem recognition
- Solution approach
- Key decisions and why

## ✅ What Was Accomplished
- Achievement 1
- Achievement 2
- Files created/modified

## 📊 What Was Created
- New files
- Changes made
- Artifacts produced

## 💡 Key Insights
- Learning 1
- Learning 2
- Connections discovered: [[Related Project]]

## 🚀 Next Steps
- Action 1
- Action 2
- Follow-up: [[Related task]]

## 🧠 Reflection
- How does this fit into bigger picture?
- What became possible?
- What surprised you?
```

## Script Details

**Location:** `~/workspace/claude_for_mac_local/tools/obsidian_summarize_session.sh`

**Input:** Session summary markdown text with `\n` for newlines

**Output:** Dated markdown file in Daily folder

**Behavior:**
- Creates Daily folder if needed
- Names file by today's date (YYYY-MM-DD.md)
- Skips if file already exists
- Preserves all markdown formatting
- Supports [[bidirectional links]]
