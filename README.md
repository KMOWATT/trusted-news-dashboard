# Trusted News Daily Dashboard

Built from the supplied **Worldwide Trusted News Sources** document. The document lists outlets by region and explicitly notes that "trusted" means broadly reputable/professionally rigorous rather than free of editorial leaning.

## What it does
- Today / This Week
- International / Climate / Investigative / Far-Right/Politics filters
- Deep Dive badge for investigative/long-form signals
- read/unread tracking in browser localStorage
- chronological feed
- static frontend
- Python RSS updater
- GitHub Actions daily refresh
- no database or paid service

## Important RSS/open-access limitation
The source document supplies websites, not RSS URLs. This project therefore includes known feed URLs where they can be identified safely and uses RSS autodiscovery for the remaining sites.

A blank/failed RSS source is reported in `feed_report.json`; it is not replaced with an invented URL.

RSS alone cannot prove that an article is completely open-access. The updater removes obvious subscription/paywall language but keeps uncertain cases. This avoids pretending that a feed entry has been fully verified when it has not.

## Local setup
1. Install Python 3.10+.
2. Open a terminal in this project.
3. Run:
   pip install -r requirements.txt
4. Run:
   python fetch_news.py
5. Serve the frontend:
   python -m http.server 8000 --directory frontend
6. Open http://localhost:8000

## GitHub Pages + automatic updates
Put the repository contents on GitHub.
Enable GitHub Pages from the repository's Pages settings and select the `main` branch `/frontend` if your Pages configuration supports that folder.

The workflow in `.github/workflows/update-news.yml` can run the updater every morning. GitHub Pages will then serve the refreshed `frontend/data/articles.json`.

If GitHub Pages only permits publishing from `/docs` or a root, move the frontend files to the publishing directory and adjust the workflow path accordingly.

## Sources
The exact source list is stored in `sources.json` and includes the outlets from the supplied document, including UK, Europe, North America, Asia-Pacific, Russia independent/exiled outlets, international broadcasters, investigative organisations, Africa and Latin America.

## Suggested maintenance
Once a month, inspect `feed_report.json`. If an outlet changes its feed or blocks RSS autodiscovery, put its current RSS URL into `sources.json`.


## GitHub Pages setup

This project is split into two parts:

- `frontend/` is the public static website and can be hosted by GitHub Pages.
- `fetch_news.py` is the Python feed collector. GitHub Actions runs it on a schedule and writes the refreshed `frontend/data/articles.json`.

### Recommended GitHub setup

1. Create a **public** GitHub repository, for example `trusted-news-dashboard`.
2. Upload the whole project, keeping the folder structure intact.
3. In **Settings → Pages**, choose **GitHub Actions** as the source.
4. The included workflow in `.github/workflows/update-news.yml` will update the news JSON each day.
5. Add a separate Pages deployment workflow if your repository does not already have one. A ready-to-paste example is included below.

### GitHub Pages deployment workflow

Create `.github/workflows/deploy-pages.yml`:

```yaml
name: Deploy News Dashboard

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v6

      - name: Setup Pages
        uses: actions/configure-pages@v5

      - name: Upload site
        uses: actions/upload-pages-artifact@v4
        with:
          path: './frontend'

      - name: Deploy
        id: deployment
        uses: actions/deploy-pages@v4
```

Then go to **Settings → Pages → Build and deployment → Source → GitHub Actions**.

### Important

GitHub Pages cannot run Python on the live website. The Python collector therefore runs in GitHub Actions, not in the browser. The browser only reads the generated `frontend/data/articles.json`.

The included collector also attempts RSS/Atom autodiscovery for sources where a direct feed URL was not specified. It deliberately does not invent feed URLs.

### News access limitation

RSS metadata cannot prove that every article is fully open-access. The collector removes obvious paywall/subscription indicators, but this is a conservative filter rather than a legal or guaranteed paywall detector.
