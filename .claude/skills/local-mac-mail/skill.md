---
name: local-mac-mail
description: Read, search, compose, and manage Apple Mail across configured accounts. Use for checking or acting on email.
user-invocable: true
---

Read and manage email via Apple Mail.

## Tools
`mail__read` `mail__get` `mail__search` `mail__list_mailboxes` `mail__list_drafts`
`mail__compose` `mail__delete` `mail__move` `mail__add_local_mailbox`

## Accounts
Account keys come from `MAIL_ACCOUNTS` in `.env` (`key:uuid:address` triples).
`local` means "On My Mac" mailboxes. If nothing is configured the tools raise a
named error — set `MAIL_ACCOUNTS`, do not hardcode addresses.

## Rules
- `mail__delete` moves to Trash but is still destructive — confirm first, and list what will go.
- Prefer `mail__search` over reading a whole mailbox.
- Summarise; never dump raw message bodies into the response.
