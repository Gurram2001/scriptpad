# Scriptpad
Static site, no build step. Scripts live in the browser; optional cloud sync via Supabase.
Files: `index.html` (page), `styles.css`, `app.js`, `config.js` (sync settings), `sw.js` (offline), `manifest.webmanifest`.

## Deploy
GitHub Pages / Netlify / Cloudflare Pages: publish this folder as-is (build command empty, publish directory `.`).
Updates reach installed copies automatically: the service worker fetches the network first and only falls back to its cache offline. No version number to bump.

## Cloud sync (optional)
1. supabase.com > New project. 2. SQL Editor > run `supabase.sql`.
3. Project Settings > API: put the Project URL and `anon` key in `config.js` (the anon key is public by design; never commit a `service_role` key).
4. Authentication > Email provider; for personal use you may turn off "Confirm email". Set Site URL to your deployed address.
5. Redeploy, then menu > Cloud sync > Create account. Sign in the same way on other devices.
Notes: last edit wins per script, so use "Save version" before big rewrites. Free Supabase projects pause after a week of inactivity (resume from the dashboard). Keep using Backup all.
Use a separate Supabase project for branch previews, and do not merge a preview's `config.js` into `main`.
The Content-Security-Policy (meta tag in `index.html`, also in `_headers`) allows `*.supabase.co`; edit both if you use a custom Supabase domain.

## Tests (92 checks, real browser)
`pip install playwright pypdf && playwright install chromium`
`python -m http.server 8765 &` then `python tests/suite.py`. GitHub Actions runs it on every push.

## Protect main (GitHub)
Settings > Branches > Add rule for `main`: require a pull request, require the "tests" status check, block force pushes.

## Single-file preview
`python scripts/inline.py > single.html`

## Security notes
Built in: strict Content-Security-Policy (own files + `*.supabase.co` only), no third-party scripts or fonts, all text inserted as plain text, every imported/restored/synced/saved script is validated and size-limited, HTTPS-only Supabase address, sign-out revokes the server session, database rows private per account (Row Level Security) with no access for signed-out visitors, CI with read-only permissions and monthly Dependabot updates.
Known limits: the sign-in token is kept in browser storage (standard for web apps; the CSP is what protects it), so use a device you trust. Scripts on your device are not encrypted. GitHub Pages cannot send HTTP headers, so there the CSP comes from the meta tag only (no clickjacking protection); Netlify/Cloudflare also apply `_headers`.
In Supabase: Authentication > Providers > Email: keep "Confirm email" on for anything beyond personal testing, set a minimum password length of 8+, and never put the `service_role` key anywhere in this repo. `tests/` and `scripts/` are served publicly with the site (they hold no secrets).
