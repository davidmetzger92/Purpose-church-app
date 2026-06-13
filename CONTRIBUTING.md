# Contributing / Maintenance Notes

A few rules that keep this app **durable and editable by non-technical staff**.
Read this before changing code.

## How the pieces fit

- **`index.html`** — the whole app (HTML/CSS/JS, no build step). Reads content at runtime from `content.json`.
- **`content.json`** — all editable content (hero, photo-band buttons, discover footer). **Owned by staff** via the `/admin` editor.
- **`/admin`** — Sveltia CMS. Staff log in with GitHub and edit `content.json` through forms; saving commits to `main`.
- **`/photos`** — images uploaded via `/admin` (or added directly).
- **GitHub Pages** serves the site from the **`main`** branch. Merging to `main` = deploying.

## The golden rule: don't hand-edit `content.json` in code branches

> `content.json` is owned by the CMS / `main`. Code/design branches change
> `index.html`, CSS, `sw.js` — **not** `content.json`.

Staff edit content through `/admin` (which commits to `main`). If a code branch
*also* edits `content.json`, the two collide and you get a merge conflict (and
risk clobbering real staff edits). Keep them separate and conflicts disappear.

**Do NOT gitignore `content.json`.** It must be committed and deployed — the CMS
writes it and the live app reads it. Gitignoring it would silently disable
editing and make the app fall back to the hardcoded defaults in `index.html`.

## When you must change the content *structure* (schema migration)

Rare — only when a redesign adds/renames content fields. To avoid losing staff
edits:

1. Pull the **latest** `content.json` from `main` first (newest staff edits).
2. Transform *that* into the new shape on your branch.
3. Merge. If `content.json` still conflicts, keep the new-schema version
   (`git checkout --ours content.json`) after confirming no real content was lost.

Also keep the hardcoded `FALLBACK` object in `index.html` in sync with the
schema, so a failed fetch still renders a usable screen.

## When you change the app shell (HTML/CSS/JS), bump the service worker

Returning users (and installed PWAs) cache the app shell. After changing
`index.html`/`sw.js`, bump `VERSION` in `sw.js` (e.g. `purpose-app-v4` →
`v5`) so the update reaches everyone on their next visit.

## Deploy flow

1. Work on a branch, open a PR.
2. Merge to `main`.
3. GitHub Pages redeploys automatically (~1 minute).
4. Hard-refresh / reopen the app to pick up the new service worker.

## Don't break these

- The `/admin` login relies on the Cloudflare Worker auth relay
  (see `SETUP-ADMIN.md`) and the GitHub OAuth app — leave `admin/config.yml`'s
  `base_url` pointed at the Worker.
- Image paths: the CMS may store them root-absolute (`/photos/x.jpg`), which
  would break under the GitHub Pages subfolder. `index.html`'s `bgVar()` strips
  the leading `/` so paths resolve relative to the page (works at subfolder,
  root, or custom domain). Keep that normalization if you refactor the render.
- Keep `manifest.json` + icons intact so PWA install keeps working.
