# Setting up the Content Editor (one-time)

The app has a no-code editor at:

> **https://davidmetzger92.github.io/Purpose-church-app/admin/**

Staff log in with GitHub and edit the buttons, links, and service times through
simple form fields. They never touch code and can't break the layout.

Because the site is "static" (no server), the login needs a tiny free helper
called an **auth relay**. You set this up **once**. After that, editing is just
"log in → change a field → Publish."

---

## What you'll create (all free)

1. A **GitHub OAuth App** — lets the editor sign people in with GitHub.
2. A **Cloudflare Worker** (the auth relay) — a ~10-line free helper that
   completes the login handshake.

You need a [GitHub](https://github.com) account (you have one) and a free
[Cloudflare](https://dash.cloudflare.com/sign-up) account.

---

## Step 1 — Create the GitHub OAuth App

1. Go to **https://github.com/settings/developers** → **OAuth Apps** →
   **New OAuth App**.
2. Fill in:
   - **Application name:** `Purpose App Editor`
   - **Homepage URL:** `https://davidmetzger92.github.io/Purpose-church-app/`
   - **Authorization callback URL:** `https://example.com/callback`
     *(temporary — you'll fix this in Step 3)*
3. Click **Register application**.
4. Copy the **Client ID**.
5. Click **Generate a new client secret** and copy it somewhere safe.

---

## Step 2 — Deploy the auth relay (Cloudflare Worker)

1. Open the ready-made relay project:
   **https://github.com/sveltia/sveltia-cms-auth** and follow its
   "Deploy to Cloudflare" instructions (one-click deploy is available).
2. When prompted, add these **environment variables / secrets**:
   - `GITHUB_CLIENT_ID` → the Client ID from Step 1
   - `GITHUB_CLIENT_SECRET` → the Client Secret from Step 1
   - `ALLOWED_DOMAINS` → `davidmetzger92.github.io`
3. After it deploys, copy the Worker URL. It looks like:
   `https://sveltia-cms-auth.your-name.workers.dev`

---

## Step 3 — Connect the pieces

1. **Update the GitHub OAuth App callback:** go back to the OAuth App from
   Step 1 and set the **Authorization callback URL** to:
   `https://YOUR-WORKER-URL.workers.dev/callback`
   (your Worker URL from Step 2, with `/callback` on the end). Save.
2. **Point the editor at your relay:** edit `admin/config.yml` in this repo and
   replace the `base_url` line with your Worker URL:
   ```yaml
   base_url: https://YOUR-WORKER-URL.workers.dev
   ```
   Commit that change (or ask Claude to do it for you).

---

## Step 4 — Give editors access

Each person who should edit needs a free GitHub account, then:

1. In this repo: **Settings → Collaborators → Add people**.
2. Add them with **Write** access. They'll get an email invite to accept.

---

## Using the editor (what staff do)

1. Visit **https://davidmetzger92.github.io/Purpose-church-app/admin/**
2. Click **Log in with GitHub** → approve.
3. Open **App Content → Home Screen**, change a field, click **Publish**.
4. The app updates automatically in about a minute.

---

## If anything ever breaks (safety net)

Content lives in a single file, `content.json`. Even if the editor or the relay
ever stops working, anyone with repo access can still edit that file directly on
GitHub (open `content.json` → pencil icon → edit → commit). The content is never
trapped inside a tool. That's the durability guarantee.
