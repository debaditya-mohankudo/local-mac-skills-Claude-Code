---
name: kaise
description: Task decomposition advisor — given any task in plain language, break it down into which skills/dispatchers to call and in what order. Use when the user asks "how do I..." or appends "/kaise" to a task.
user-invocable: true
---

# kaise — How to do this?

When invoked, the user has described a task (either before `/kaise` or as an argument after it). Your job is to decompose it into a **step-by-step dispatcher plan** using the skills and MCP tools available in this environment.

---

## Output format

Always respond with this structure — no preamble, no explanation prose:

```
**Task:** <restate the task in one line>

**Steps:**
1. <skill or dispatcher> — <what it does in this context>
2. ...
N. <optional: confirm with user / surface result>

**Guardrails:**
- <any confirmation, privacy, or safety steps required>
```

Keep each step to one line. Be specific about which tool/skill handles it.

---

## Available Skills & Dispatchers

### Communication
| Skill | Dispatcher / Tool | Use for |
|-------|-------------------|---------|
| `/local-mac-contacts` | `contacts_search(name=...)` | Resolve a name → phone/email |
| `/local-mac-imessage` | `imessage_send(recipient, message)` | Send iMessage |
| `/local-mac-imessage` | `imessage_read(limit)` | Read recent iMessages |
| `/local-mac-mail` | `mail_read(folder, limit)` | Read emails |
| `/local-mac-call` | `call(number)` | Make a phone call |

### Productivity
| Skill | Dispatcher / Tool | Use for |
|-------|-------------------|---------|
| `/local-mac-calendar` | `calendar_read / calendar_create / calendar_delete` | Read/add/remove events |
| `/local-mac-reminders` | `reminders_read / reminders_create` | Read/add reminders |
| `/local-mac-vault` | `obsidian_read / obsidian_create / obsidian_search / obsidian_tasks` | All Obsidian vault ops |
| `/local-mac-vault capture-session` | `obsidian_create / obsidian_append` | Save Claude session to daily note |

### Media & Apps
| Skill | Dispatcher / Tool | Use for |
|-------|-------------------|---------|
| `/local-mac-music` | `music_control(action, ...)` | Play/pause/skip/volume/playlist |
| `/local-mac-safari` | `safari_open / safari_read / safari_js` | Browse, scrape, automate web |
| `/local-mac-notify` | `notify(title, message)` | macOS desktop notification |
| `/local-mac-whisper` | `whisper_transcribe(file)` | Transcribe audio file |

### System
| Skill | Dispatcher / Tool | Use for |
|-------|-------------------|---------|
| `/local-mac-wifi` | `wifi_status / wifi_connect` | Check/switch Wi-Fi |
| `/local-mac-sleep` | `sleep_mac()` | Put Mac to sleep |
| `/local-mac-process` | `process_list / process_kill` | List/kill processes |
| `/local-mac-storage` | `storage_info()` | Disk usage |
| `/local-mac-network` | `network_info()` | Network diagnostics |
| `/local-mac-screencapture` | `screencapture()` | Take screenshot |
| `/local-mac-ssh` | `ssh_run(host, cmd)` | Run command over SSH |

### Market Intelligence
| Skill | Dispatcher / Tool | Use for |
|-------|-------------------|---------|
| `/market-intel-live-prices` | `get_prices(symbols)` | Live stock/index prices |
| `/market-intel-morning-brief` | full pipeline | Morning market summary |
| `/market-intel-evening-brief` | full pipeline | Evening market summary |
| `/market-intel-portfolio-check` | vault + prices | Portfolio P&L snapshot |
| `/market-intel-fii-dii-check` | `get_fii_dii()` | FII/DII activity |
| `/market-intel-nifty-analysis` | chart + analysis | Nifty technical view |
| `/market-intel-gold` | `get_gold_price()` | Gold price |
| `/market-intel-live-news` | `get_news(query)` | Live market news |

### Dev / Git
| Skill | Dispatcher / Tool | Use for |
|-------|-------------------|---------|
| `/gc-gp` | `git_local.sh -y [--push]` | Commit and optionally push |
| `/k-investigate` | web search + K framework | Deep geopolitical/strategic inquiry |
| `/apfel-vault-chat` | Apfel LLM + vault notes | Summarize vault content on-device |

---

## Guardrail rules (always apply)

- **iMessage send** → always confirm with user before sending
- **Call** → always confirm before dialing
- **Calendar delete / Reminder delete** → always confirm
- **Vault write** → use `obsidian_create` or `obsidian_append` — never direct filesystem write
- **Git commit** → always use `/gc-gp`, never raw `git`
- **Personal data** → never hardcode; reference `.env` or vault

---

## Examples

**Task:** Send message to Simran
```
Task: Send iMessage to Simran

Steps:
1. /local-mac-contacts → contacts_search(name="Simran") — resolve name to phone number
2. (if multiple matches) → ask user to pick one
3. /local-mac-imessage → compose message, confirm recipient + message text with user
4. imessage_send(recipient=<phone>, message=<text>) — send on confirmation

Guardrails:
- Never send without explicit user confirmation
- If contact not found, surface error and ask user for phone number directly
```

**Task:** Add a reminder to call dentist tomorrow
```
Task: Create reminder — call dentist tomorrow

Steps:
1. /local-mac-time → resolve "tomorrow" to absolute date (IST)
2. /local-mac-reminders → reminders_create(title="Call dentist", due=<date>)
3. Confirm to user: reminder created

Guardrails:
- No confirmation needed for create (non-destructive)
```

**Task:** What's Nifty doing today?
```
Task: Nifty market status

Steps:
1. /market-intel-live-prices → get_prices(["^NSEI"]) — current index level
2. /market-intel-nifty-analysis → chart + technical analysis
3. /market-intel-live-news → get_news("Nifty") — top headlines

Guardrails:
- No financial data outside vault
```
