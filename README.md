# Scriptpad
Static site: no build step. Change `V` in sw.js each release so installed copies update.

## Deploy (pick one)
- Cloudflare Pages / Netlify: push this folder to a Git repo, connect it, build command empty, output directory `/`. Add your domain in the dashboard.
- GitHub Pages: push to a repo, Settings > Pages > deploy from branch (root).
- Docker: `FROM nginx:alpine` + `COPY . /usr/share/nginx/html`.
HTTPS is required for install and offline mode (all three above provide it).

## Notes
- Scripts are stored in the browser (localStorage). Use Fountain > Backup all regularly, or Download.
- PDF export loads jsPDF from cdnjs once, then the service worker caches it for offline use.
