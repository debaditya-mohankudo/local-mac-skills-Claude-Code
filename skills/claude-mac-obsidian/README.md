# claude-mac-obsidian

A Claude skill for reading and writing Obsidian markdown notes with full support for bidirectional links and note organization.

## Features

- **Bidirectional Links** — Support for `[[note-name]]` syntax
- **Markdown Support** — Full Markdown formatting preserved
- **Folder Organization** — Create notes in subdirectories (e.g., `Projects/My Project`)
- **Link Analysis** — Extract forward links and find backlinks
- **Obsidian Compatible** — All notes stored in `~/Documents/claude_documents` ready for Obsidian vault

## Usage

### Read a Note
```bash
/claude-mac-obsidian read "Note Name"
```

### Write or Update a Note
```bash
/claude-mac-obsidian write "Note Name" "# Content\n\nWith [[links]]"
```

### List All Notes
```bash
/claude-mac-obsidian list
```

### Find Forward Links
```bash
/claude-mac-obsidian links "Note Name"
```

### Find Backlinks (Notes Referencing a Note)
```bash
/claude-mac-obsidian backlinks "Note Name"
```

### Delete a Note
```bash
/claude-mac-obsidian delete "Note Name"
```

## Example Workflow

1. Create a main project note with links:
   ```bash
   /claude-mac-obsidian write "My Project" "# My Project\n\nMain overview.\n\nSee [[Tasks]] and [[Progress]]"
   ```

2. Create linked notes:
   ```bash
   /claude-mac-obsidian write "Tasks" "# Tasks\n\nWork on [[My Project]]"
   /claude-mac-obsidian write "Progress" "# Progress\n\nTracking [[My Project]]"
   ```

3. Analyze the knowledge graph:
   ```bash
   /claude-mac-obsidian links "My Project"        # Shows: Tasks, Progress
   /claude-mac-obsidian backlinks "My Project"    # Shows: Tasks, Progress
   ```

4. View all notes:
   ```bash
   /claude-mac-obsidian list
   ```

## Storage Location

All notes are stored in: `~/Documents/claude_documents`

This folder is fully compatible with Obsidian. You can:
- Open it as a vault in Obsidian desktop app
- Manually edit notes in any text editor
- Use Obsidian's graph view to visualize your knowledge graph

## Note Names

- Use without `.md` extension (automatically added)
- Spaces are supported: `My Note` → `My Note.md`
- Folder paths are supported: `Projects/My Project` → `Projects/My Project.md`
- Bidirectional links are case-sensitive: `[[My Project]]` will not match `[[my project]]`

## Scripts

This skill uses the following shell scripts from `tools/`:

| Script | Purpose |
| ------ | ------- |
| `obsidian_read.sh` | Read a note |
| `obsidian_write.sh` | Write/update a note |
| `obsidian_list.sh` | List all notes |
| `obsidian_delete.sh` | Delete a note (with confirmation) |
| `obsidian_links.sh` | Extract forward links from a note |
| `obsidian_backlinks.sh` | Find backlinks to a note |
