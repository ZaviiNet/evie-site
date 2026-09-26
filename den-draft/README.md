# Den — front-end prototype

**Status:** non-functional. No backend, no network calls, nothing stored (except a role hint in
`localStorage` so the two roles can be previewed). This exists to agree on the *shape* before any
backend gets written.

## Pages

| Page | What it's for |
|---|---|
| `index.html` | Login. Email + magic-link wording, with the two roles previewable. |
| `room.html` | **The core.** Shared transcript, mention highlighting, composer, command hints, context meter, file chips. |
| `projects.html` | Projects (each with Chat / Files / Docs) vs sessions — they are related, not the same. |
| `dashboard.html` | Ops: health, spend, run history, audit log, emergency stop. |
| `admin.html` | Den settings only — bridge, limits, people, Discord mirror, danger zone. |
| `providers.html` | Providers & models — credential status first, because that is what actually breaks. |
| `bots.html` | AI bots — add/edit/delete a bot: role, provider, model, persona, caps. Text-only is locked, not a toggle. |

## Things to try

1. **Log in as each role** (index page) and open the room. The banner shows which role you're previewing.
2. **Type a normal message** — it stays between the two humans. No reply. That is the mechanic.
3. **Type `@evie`** in a message — after a beat, "Evie" answers. Only mentions pull her in.
4. **Type `/`** — the command palette opens. On the room page, `/stop` is refused while previewing as GT, and the refusal is shown as a *server* rejection rather than a reply from me.
5. **Click `/new`, `/clear`, `/plan`, `/status`** — each fakes its effect and says what it actually touches.
6. **Attach (📎)** — shows what the real upload path does (staged privately, ≤16 MiB, 24 h TTL).
7. **Bots page** — try deleting `@skeptic`; note it archives, because a hard delete would break every past transcript that mentions it.
8. **Dashboard** — the run-history table includes a run aborted by a closed socket, and the audit log is the shape I'd want when something goes wrong at 2am.
8. **Admin** — note what it can't do: it has no control over the agent's tools or prompts. That's deliberate and load-bearing.

## Roles

- **Zavii (owner)** — full authority, unchanged from Discord. Only the owner can `/stop` and use the admin/danger controls.
- **GT (guest)** — talk, upload, mention. Guest-triggered runs use a restricted tool set (no shell, no memory writes), enforced in the agent's configuration rather than requested in a prompt.
- **Evie** — reads everything as context, answers on mention, and reads uploaded files themselves.

## Feedback I'm looking for

1. **The room layout** — is the transcript/composer/sidebar split right for two people thinking out loud?
2. **Mention mechanics** — obvious enough that GT won't accidentally talk to me, and I won't butt into a conversation?
3. **Do the pages match the site's feel**, or does it look like a different product?
4. **Anything missing** you'd want on day one — and anything here you'd cut.
5. **The admin page's boundary** — is "configures Den, never the agent" the right line, or too strict?
6. **Sessions** — one long room, or a room per topic?

## Notes

- `noindex, nofollow` on every page — this is a draft, not a launch.
- No external dependencies, no build step, no frameworks. The site is dependency-free and this stays the same way.
- Theme tokens are copied from `eviethegremlinn.com` so a restyle later is one file.
