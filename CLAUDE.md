# Oto

CLI unifié pour automatiser des tâches, utilisé par des humains et des agents AI via Bash.

## Pourquoi ce projet

On avait un monorepo `otomata` (`/data/projects/otomata/`) devenu bordélique :
- `tools/otomata-tools/otomata/` imbriqué sur 3 niveaux pour un simple package Python
- `cli.py` monolithique de 1193 lignes avec toutes les commandes
- `_legacy/` mort traîné depuis des mois
- LinkedIn mélangé avec le reste
- Noms de comptes Google incohérents (`default`, `gmail` qui pointaient sur le même email)

On a tout repris de zéro dans `/data/oto` avec un package propre nommé `oto`.

## Philosophie

- **CLI-first** : tout passe par `oto <commande>`, pas de MCP, pas de serveur pour les outils
- **Pour les agents AI** : output JSON sur stdout, erreurs sur stderr, composable avec pipes
- **Backends configurables** (à venir) : chaque groupe de commandes pourra être routé vers un CLI externe (ex: `gog` pour Google) au lieu du client Python intégré. Inspiré d'OpenClaw où les "skills" (markdown) enseignent aux agents quelles commandes utiliser et les "tools" sont les CLIs sur la machine
- **Pas de sur-ingénierie** : pas de plugin registry, pas d'ABC, pas de MCP. Un if/else dans les commandes suffit

## Stack

- Python 3.10+, Typer (CLI), Hatchling (build)
- Google APIs (auth, drive, docs, sheets, slides, gmail, keep)
- Patchright/o-browser (browser automation)
- Requests (HTTP), python-dotenv (secrets)

## Architecture

```
/data/oto/
├── oto/                        # Package Python
│   ├── __init__.py             # v0.1.0
│   ├── cli.py                  # Assembleur Typer + main() error handler
│   ├── config.py               # Secrets 3-tier
│   ├── commands/               # 1 fichier par domaine
│   │   ├── google.py           # drive, docs, sheets, slides, gmail, auth
│   │   ├── notion.py           # search, page, database
│   │   ├── browser.py          # linkedin, crunchbase, pappers, indeed, g2
│   │   ├── sirene.py           # SIRENE API (search, get, stock)
│   │   ├── search.py           # web, news (serper)
│   │   ├── enrichment.py       # kaspr, hunter, lemlist
│   │   ├── pennylane.py        # comptabilité
│   │   ├── anthropic.py        # usage, cost, summary
│   │   ├── company.py          # SIREN lookup multi-source
│   │   └── skills.py           # Claude Code skills management (enable/disable)
│   └── tools/                  # 32 modules clients API
│       ├── google/             # gmail/, drive/, docs/, sheets/, slides/, keep/, credentials.py
│       ├── sirene/
│       ├── browser/
│       ├── common/
│       ├── anthropic/
│       ├── kaspr/, hunter/, lemlist/
│       ├── pennylane/
│       └── ... (apollo, attio, folk, figma, groq, etc.)
├── cloud/                      # PAS ENCORE MIGRÉ — voir issues #8 #9
├── skills/                     # Claude Code skills (source de vérité)
│   └── oto-*/SKILL.md          # 8 skills, symlinked vers ~/.claude/skills/
├── pyproject.toml              # entry point: oto = "oto.cli:main"
├── venv/                       # virtualenv local
└── PLAN.md                     # Plan détaillé de restructuration
```

## Commandes

```bash
# Installation
pip install -e .                              # deps de base
pip install -e ".[all]"                       # toutes les deps optionnelles

# Exemples
oto --help
oto google gmail-search "from:nicolas" -a otomata -n 5
oto google gmail-send "dest@email.com" "Sujet" "Corps" -a otomata
oto google gmail-archive -q "subject:newsletter" -a perso
oto google auth --list
oto google auth moncompte                     # lance OAuth flow dans le browser
oto sirene search "otomata"
oto browser linkedin-profile "https://linkedin.com/in/someone"
oto search web "AI agents 2026"
oto config                                    # affiche secrets détectés

# Skills Claude Code
oto skills list                              # skills disponibles + statut
oto skills enable --all                      # active tous les skills (symlinks)
oto skills disable oto-pennylane             # désactive un skill
```

## Comptes Google OAuth

Les tokens sont dans `~/.otomata/google-oauth-token-{name}.json`.

| Compte | Email | Usage |
|--------|-------|-------|
| `otomata` | alexis@otomata.tech | Compte pro |
| `perso` | alexis.laporte@gmail.com | Compte perso |
| `sarahetalexis` | sarah.et.alexis.sl@gmail.com | Compte famille |

**ATTENTION** : il n'existe PAS de compte `default` ni `gmail`. Ces anciens noms ont été supprimés/renommés. Utiliser `-a otomata` ou `-a perso`.

Pour ajouter un compte : `oto google auth <nom>` → ouvre le browser pour le flow OAuth.

## Secrets

Résolution 3-tier (premier trouvé gagne) :
1. Variables d'environnement
2. `.otomata/secrets.env` dans le projet (remonte 4 niveaux)
3. `~/.otomata/secrets.env` (user-level)

Secrets utilisés : `GOOGLE_SERVICE_ACCOUNT`, `GOOGLE_OAUTH_CLIENT`, `NOTION_API_KEY`, `LINKEDIN_COOKIE`, `SIRENE_API_KEY`, `SERPER_API_KEY`, `KASPR_API_KEY`, `HUNTER_API_KEY`, `LEMLIST_API_KEY`, `PENNYLANE_API_KEY`, `GROQ_API_KEY`, `ANTHROPIC_ADMIN_API_KEY`.

Le fichier OAuth client Google est dans `~/.otomata/google-oauth-client.json`.

## Pattern pour les commandes

Chaque fichier `commands/*.py` :
```python
import typer
import json
from typing import Optional

app = typer.Typer()

@app.command("gmail-search")
def gmail_search(
    query: str = typer.Argument(..., help="Gmail search query"),
    account: Optional[str] = typer.Option(None, "--account", "-a"),
    max_results: int = typer.Option(20, "--max-results", "-n"),
):
    """Search Gmail messages."""
    from oto.tools.google.gmail.lib.gmail_client import GmailClient
    client = GmailClient(account=account)
    results = client.search(query=query, max_results=max_results)
    print(json.dumps(results, indent=2))
```

Points clés :
- `app = typer.Typer()` exporté, assemblé dans `cli.py` via `app.add_typer()`
- Imports des clients **locaux** (dans la fonction, pas en haut du fichier) pour que le CLI reste rapide
- Toujours `print(json.dumps(..., indent=2))` pour l'output
- Erreurs de secrets manquants catchées dans `main()` → message propre sur stderr (pas de traceback)

## Provenance

Migré depuis `/data/projects/otomata/tools/otomata-tools/otomata/` (renommé `_MIGRATED_TO_OTO`).
- Package renommé de `otomata` à `oto`
- Tous les imports `from otomata.` → `from oto.`
- `cli.py` monolithique splitté en 10 fichiers commands/
- Les clients API dans `tools/` sont copiés tels quels (pas de refactor)

Le monorepo `/data/projects/otomata/` contient encore les composants pas migrés : app, worker, viewer, extension, linkedin.

## Issues GitHub (AlexisLaporte/oto)

| # | Titre | Statut |
|---|-------|--------|
| 1 | Migrer les clients API dans oto/tools/ | done |
| 2 | Split cli.py en commands/ | done |
| 10 | pyproject.toml + fix imports | done |
| 8 | Regrouper cloud/ (app, worker, viewer, extension) | todo — migrer depuis /data/projects/otomata/ |
| 9 | Nettoyer legacy + déplacer linkedin | todo |
| 11 | Config poste + projet (config.yaml) | later |
| 7 | Backend CLI externe configurable | later |

## Ce qu'on ne fait PAS

- Pas de refactor des clients API existants (tools/* = tel quel)
- Pas de plugin registry / ABC / interfaces
- Pas de MCP
- Pas de backward compat — on casse, on recommence propre
- Pas de fallbacks, pas de code legacy
- Pas de fichiers > 500 lignes

## Prod

- `otomata.tech` → tuls.me:3013
- `otomata.tuls.me` → Flask app (cloud/app/, port 5000)
- Serveur : 51.15.225.121 (ssh alexis)
