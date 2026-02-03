# Otomata Tools

Bibliothèque Python d'outils d'automatisation. Projet public (pas de secrets).

## Structure

```
otomata/tools/
├── browser/          # Lib browser automation (Patchright)
├── collective/       # Client Collective.work (browser-based)
├── google/           # Client Google Workspace (API)
└── notion/           # Client Notion (API)
```

## Types de clients

| Type | Transport | Exemples |
|------|-----------|----------|
| **API** | HTTP REST/SDK | google/, notion/ |
| **Browser** | Patchright (Playwright) | collective/ |

Les clients browser sont utilisés quand il n'y a pas d'API publique.

## Browser automation

```python
from otomata.tools.browser import BrowserClient

async with BrowserClient(profile_path="~/.cache/my-session") as browser:
    await browser.goto("https://example.com")
    text = await browser.get_text()
```

**Session** : le `profile_path` contient cookies/localStorage. Permet de réutiliser une session authentifiée.

**Note** : les sessions sont stockées côté utilisateur (ex: `~/.cache/browser-session-xxx`), pas dans ce repo.

## Collective client

```python
from otomata.tools.collective import CollectiveClient

client = CollectiveClient(profile_path="~/.cache/browser-session-xxx")
result = await client.scrape_jobs(url="https://app.collective.work/...")
```

CLI :
```bash
python -m otomata.tools.collective.client \
  --url "https://app.collective.work/..." \
  --profile ~/.cache/browser-session-xxx \
  -o output.json
```

## Installation

```bash
pip install -e .              # Base (google, notion)
pip install -e ".[browser]"   # + browser automation (patchright)
```

## Roadmap

Voir `TODO.md` pour les idées (notamment Vercel agent-browser comme alternative à Patchright).
