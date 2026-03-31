---
name: local-mac-safari
description: Control Safari on macOS — open URLs, read page content, run JavaScript, click/fill elements, list tabs, take screenshots. Use when user asks to browse, scrape, automate, or interact with a web page in Safari.
user-invocable: true
---

Control Safari on macOS via AppleScript + JavaScript execution. No API token, no Playwright, no browser driver needed.

> **Requirement:** Enable JavaScript from Apple Events in Safari:
> Safari → Develop → Allow JavaScript from Apple Events
> (If Develop menu is hidden: Safari → Settings → Advanced → Show Develop menu)

---

## Navigation

```bash
~/workspace/claude_for_mac_local/tools/safari_control.sh open "https://example.com"
~/workspace/claude_for_mac_local/tools/safari_control.sh current-url
~/workspace/claude_for_mac_local/tools/safari_control.sh current-title
~/workspace/claude_for_mac_local/tools/safari_control.sh reload
~/workspace/claude_for_mac_local/tools/safari_control.sh back
~/workspace/claude_for_mac_local/tools/safari_control.sh forward
```

## Tab management

```bash
~/workspace/claude_for_mac_local/tools/safari_control.sh list-tabs
~/workspace/claude_for_mac_local/tools/safari_control.sh close-tab
~/workspace/claude_for_mac_local/tools/safari_control.sh close-all-tabs
```

## Read page content

```bash
~/workspace/claude_for_mac_local/tools/safari_read.sh text       # full page text (innerText)
~/workspace/claude_for_mac_local/tools/safari_read.sh html       # full page HTML
~/workspace/claude_for_mac_local/tools/safari_read.sh links      # all links (href + label)
~/workspace/claude_for_mac_local/tools/safari_read.sh title      # page title
~/workspace/claude_for_mac_local/tools/safari_read.sh selected   # currently selected text
```

## Run JavaScript

Execute any JS in the current tab and return the result:

```bash
~/workspace/claude_for_mac_local/tools/safari_js.sh "JAVASCRIPT"
```

### Common JS patterns

**Click an element by selector:**
```bash
~/workspace/claude_for_mac_local/tools/safari_js.sh "document.querySelector('button.submit').click()"
```

**Fill a form field:**
```bash
~/workspace/claude_for_mac_local/tools/safari_js.sh "document.querySelector('input[name=email]').value = 'test@example.com'"
```

**Submit a form:**
```bash
~/workspace/claude_for_mac_local/tools/safari_js.sh "document.querySelector('form').submit()"
```

**Scroll to bottom:**
```bash
~/workspace/claude_for_mac_local/tools/safari_js.sh "window.scrollTo(0, document.body.scrollHeight)"
```

**Extract specific element text:**
```bash
~/workspace/claude_for_mac_local/tools/safari_js.sh "document.querySelector('h1').innerText"
```

**Wait for element (poll loop):**
```bash
~/workspace/claude_for_mac_local/tools/safari_js.sh "document.querySelector('.result') ? document.querySelector('.result').innerText : 'NOT READY'"
```

## Screenshot

```bash
~/workspace/claude_for_mac_local/tools/safari_control.sh screenshot /tmp/page.png
```

## Playwright-replacement workflow

For tasks that would normally use Playwright:

1. `safari_control.sh open URL` — navigate
2. `safari_read.sh text` or `safari_read.sh html` — read content
3. `safari_js.sh "..."` — interact (click, fill, submit)
4. Repeat steps 2–3 as needed
5. `safari_control.sh screenshot` — capture result

## Tab tracking — MANDATORY

**Before opening any URL, record it in a temp file. Close all tracked tabs at the end.**

### Step 1 — Before opening the first tab, snapshot existing tabs:
```bash
~/workspace/claude_for_mac_local/tools/safari_control.sh list-tabs > /tmp/safari_tabs_before.txt
```

### Step 2 — Log every URL you open:
```bash
echo "https://example.com" >> /tmp/safari_tabs_opened.txt
~/workspace/claude_for_mac_local/tools/safari_control.sh open "https://example.com"
```

### Step 3 — After task is complete, close ALL tabs you opened:
```bash
# Count how many URLs were opened
COUNT=$(wc -l < /tmp/safari_tabs_opened.txt)
for i in $(seq 1 $COUNT); do
  ~/workspace/claude_for_mac_local/tools/safari_control.sh close-tab
done
# Cleanup temp files
rm -f /tmp/safari_tabs_opened.txt /tmp/safari_tabs_before.txt
```

### Step 4 — Verify cleanup:
```bash
~/workspace/claude_for_mac_local/tools/safari_control.sh list-tabs
# Should match the original tabs from Step 1
```

**Rules:**
- Use `safari_control.sh open URL` for each URL — this reuses the current tab (sequential navigation, no new tabs opened). Each `open` counts as 1 tab to close.
- Never leave Safari tabs open after a skill run.
- If the task is interrupted, still run Step 3 cleanup before exiting.

## Guardrails

- **URL allowlist enforced** — `safari_control.sh open` refuses any URL whose domain is not in `~/workspace/claude_for_mac_local/safari_config.sh`. If blocked, tell the user to add the domain to `ALLOWED_URLS`. To disable entirely, set `DISABLE_ALLOWLIST=true` in that file — warn the user this removes all URL restrictions.
- Safari must be open. If AppleScript errors, tell the user to open Safari first.
- JavaScript from Apple Events must be enabled in Safari Develop menu.
- Never submit forms or take destructive actions without confirming with the user.
- Page reads can be large — summarize or extract relevant sections rather than dumping full HTML.
- Do not store or log any credentials entered via `safari_js.sh`.
