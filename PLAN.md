# Plan : Restructuration monorepo Otomata

## Contexte

Le monorepo `/data/projects/otomata/` est un foutoir : `_legacy/` mort, `tools/otomata-tools/` imbriqué inutilement, `cli.py` monolithique (1193 lignes), LinkedIn mélangé avec le reste. On restructure tout proprement. Le CLI est renommé `oto` (plus court à taper). On casse tout, on recommence propre.

Inspiré d'OpenClaw : les "skills" enseignent à l'agent quelles commandes utiliser, les "tools" sont les CLIs installées sur la machine. On veut pouvoir configurer des backends CLI externes (ex: `gog` pour Google).

## Structure actuelle

```
/data/projects/otomata/
├── _legacy/                    # MORT — à supprimer
├── app/                        # Webapp Flask + plugins + tools (20+)
├── extension/                  # Browser extension JS
├── infra/                      # Config infra (local/start.sh)
├── linkedin/                   # LinkedIn app — à sortir du monorepo
├── tools/                      # CLI otomata
│   ├── otomata-tools/
│   │   ├── otomata/
│   │   │   ├── cli.py          # 1193 lignes monolithiques
│   │   │   ├── config.py       # Secrets 3-tier
│   │   │   └── tools/          # 32 clients API
│   │   └── pyproject.toml
│   └── venv/
├── viewer/                     # File format rendering
└── worker/                     # Task execution + agent SDK
```

## Structure cible

```
/data/projects/otomata/
├── oto/                        # Package CLI (ex tools/otomata-tools/otomata/)
│   ├── __init__.py
│   ├── cli.py                  # Assembleur (~30 lignes)
│   ├── config.py               # Secrets + config poste/projet
│   ├── backends.py             # Wrapper CLI externes (~80 lignes)
│   ├── commands/               # Commandes CLI par domaine
│   │   ├── __init__.py
│   │   ├── google.py           # drive-*, docs-*, gmail-*, sheets-*, slides-*, auth (~210 lignes)
│   │   ├── notion.py           # search, page, database (~55 lignes)
│   │   ├── browser.py          # linkedin-*, crunchbase, pappers, indeed, g2 (~240 lignes)
│   │   ├── sirene.py           # search, get, siret, headquarters, stock-* (~200 lignes)
│   │   ├── search.py           # web, news (~35 lignes)
│   │   ├── enrichment.py       # kaspr, hunter, lemlist (~150 lignes)
│   │   ├── pennylane.py        # company, fiscal-years, trial-balance (~100 lignes)
│   │   ├── anthropic.py        # usage, cost, summary, today (~65 lignes)
│   │   └── company.py          # company SIREN lookup (~20 lignes)
│   └── tools/                  # Clients API (inchangés, déplacés)
│       ├── google/             # gmail, drive, docs, sheets, slides, keep
│       ├── sirene/
│       ├── browser/
│       ├── common/
│       └── ... (32 modules existants)
├── cloud/                      # App web + worker + viewer
│   ├── app/                    # (ex app/) — webapp Flask, plugins
│   ├── worker/                 # (ex worker/) — task execution, agent SDK
│   ├── viewer/                 # (ex viewer/) — file format rendering
│   └── extension/              # (ex extension/) — browser extension
├── infra/                      # Inchangé
├── pyproject.toml              # Package config unique
└── CLAUDE.md
```

**Déplacé hors monorepo :** `linkedin/` → `/data/projects/linkedin-assistant/`
**Supprimé :** `_legacy/`, `tools/` (après migration)

---

## Phase 1 : Réorganisation fichiers

### 1a. Créer `oto/` et migrer les clients API
```
mkdir -p oto/commands
cp -r tools/otomata-tools/otomata/tools/ oto/tools/
cp tools/otomata-tools/otomata/config.py oto/config.py
cp tools/otomata-tools/otomata/__init__.py oto/__init__.py
```

### 1b. Split cli.py → commands/

Extraire `tools/otomata-tools/otomata/cli.py` (1193 lignes) en 9 fichiers.

Chaque fichier de commande suit le pattern :
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

| Fichier | Commandes | ~lignes |
|---------|-----------|---------|
| `google.py` | drive-list, drive-get, drive-download, docs-get, docs-create, sheets-read, sheets-write, slides-get, gmail-search, gmail-read, gmail-send, gmail-draft, gmail-archive, gmail-trash, gmail-attachments, auth | 210 |
| `notion.py` | search, page, database | 55 |
| `browser.py` | linkedin-profile, linkedin-company, linkedin-search, linkedin-people, linkedin-employees, linkedin-posts, crunchbase, pappers, indeed, g2 | 240 |
| `sirene.py` | search, get, siret, headquarters, suggest-naf, entreprises, stock-download, stock-addresses | 200 |
| `search.py` | web, news | 35 |
| `enrichment.py` | kaspr, hunter, lemlist-search, lemlist-enrich, lemlist-verify | 150 |
| `pennylane.py` | company, fiscal-years, trial-balance, general-ledger, customer-invoices, supplier-invoices | 100 |
| `anthropic.py` | usage, cost, summary, today | 65 |
| `company.py` | company (SIREN lookup multi-source) | 20 |

### 1c. Nouveau `oto/cli.py` assembleur

```python
import typer

app = typer.Typer(
    name="oto",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)

from oto.commands import google, notion, browser, sirene, search, enrichment, pennylane, anthropic, company

app.add_typer(google.app, name="google")
app.add_typer(notion.app, name="notion")
app.add_typer(browser.app, name="browser")
app.add_typer(sirene.app, name="sirene")
app.add_typer(search.app, name="search")
app.add_typer(enrichment.app, name="enrichment")
app.add_typer(pennylane.app, name="pennylane")
app.add_typer(anthropic.app, name="anthropic")

# Commandes top-level
app.command("company")(company.company)
```

### 1d. Regrouper cloud/
```
mkdir cloud
mv app/ cloud/app/
mv worker/ cloud/worker/
mv viewer/ cloud/viewer/
mv extension/ cloud/extension/
```

### 1e. Nettoyer
```
rm -rf _legacy/
mv linkedin/ /data/projects/linkedin-assistant/
rm -rf tools/
```

### 1f. `pyproject.toml` à la racine

Reprendre les deps de `tools/otomata-tools/pyproject.toml` :
```toml
[project]
name = "oto"
version = "0.5.0"
requires-python = ">=3.10"
dependencies = [
    "typer>=0.9.0",
    "requests",
    "python-dotenv",
    "google-auth",
    "google-auth-oauthlib",
    "google-api-python-client",
    "pyyaml",
    # ... (reprendre toutes les deps existantes)
]

[project.scripts]
oto = "oto.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### 1g. Fix imports
- `from otomata.` → `from oto.` dans tout `oto/` (search & replace)
- `from otomata.tools.` → `from oto.tools.`
- Vérifier `cloud/app/` et `cloud/worker/` pour les imports otomata

---

## Phase 2 : Config poste + projet

Ajouter dans `oto/config.py` (~30 lignes supplémentaires) :

```yaml
# ~/.otomata/config.yaml — config poste (machine-level)
google:
  default_account: default

# .otomata.yaml — config projet (dans un repo)
google:
  default_account: perso
```

```python
def get_tool_config(tool_name: str) -> dict:
    """Get merged config for a tool. Resolution: project > machine > default."""
    import yaml
    config = {}

    # Machine-level
    machine_path = Path.home() / ".otomata" / "config.yaml"
    if machine_path.exists():
        with open(machine_path) as f:
            machine = yaml.safe_load(f) or {}
        config.update(machine.get(tool_name, {}))

    # Project-level (override)
    project_path = _find_project_config()
    if project_path:
        with open(project_path) as f:
            project = yaml.safe_load(f) or {}
        config.update(project.get(tool_name, {}))

    return config
```

**Fichier modifié :** `oto/config.py` (+30 lignes)

---

## Phase 3 : Backend CLI externe

Permettre de router certaines commandes vers un CLI externe. Pas un système de plugins — juste un if/else dans les commandes qui ont un backend alternatif.

### Config

```yaml
# ~/.otomata/config.yaml
google:
  backend: gog      # utiliser `gog` CLI au lieu du client Python
  # OU
  backend: builtin  # défaut, client Python intégré
```

### `oto/backends.py` (~80 lignes)

```python
import subprocess
import json

def run_external(cmd: list[str]) -> dict:
    """Execute an external CLI, parse JSON stdout."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return json.loads(result.stdout)
```

### Pattern dans les commandes

```python
# oto/commands/google.py
@app.command("gmail-search")
def gmail_search(query: str, account: str = None):
    config = get_tool_config("google")
    if config.get("backend") == "gog":
        cmd = ["gog", "gmail", "search", query]
        if account:
            cmd += ["--account", account]
        result = run_external(cmd)
    else:
        from oto.tools.google.gmail.lib.gmail_client import GmailClient
        client = GmailClient(account=account)
        result = client.search(query=query)
    print(json.dumps(result, indent=2))
```

Seules les commandes Google auraient un backend `gog` pour l'instant. La majorité des commandes (browser, sirene, enrichment...) n'ont pas d'alternative et restent inchangées.

**Fichiers créés/modifiés :**
- `oto/backends.py` → nouveau (~80 lignes)
- `oto/commands/google.py` → modifié (ajout des if backend)

---

## Phase 4 : Install global + compte Gmail perso

1. `pip install -e /data/projects/otomata` (ou `pipx install -e .`)
2. `oto google auth --account perso` → flow OAuth pour alexis.laporte@gmail.com
3. `oto google gmail-archive -q 'subject:"Quote request"' -a perso`

---

## Ce qu'on ne fait PAS

- Pas de refactor des clients API (tools/* déplacés tels quels)
- Pas de plugin registry / ABC / interfaces
- Pas de MCP
- Pas de backward compat (on casse, on recommence propre)
- Pas d'auto-détection magique de CLIs

## Ordre d'exécution

1. **Phase 1a-1c** : Créer `oto/`, migrer tools, split cli.py → commandes
2. **Phase 1d** : Regrouper cloud/
3. **Phase 1e-1f** : Nettoyer + pyproject.toml racine
4. **Phase 1g** : Fix imports (`otomata` → `oto`)
5. **Phase 4** : `pip install -e .` + vérification
6. **Phase 2** : Config poste/projet (quand nécessaire)
7. **Phase 3** : Backends CLI externes (quand on installe gog)

## Vérification

- `pip install -e .` depuis la racine
- `oto --help` → tous les groupes listés
- `oto google gmail-search "test" -a otomata` → fonctionne
- `oto google gmail-archive <id> -a perso` → archive
- `oto sirene search "test"` → fonctionne
- `oto browser linkedin-profile "url"` → fonctionne
- Chaque commande existante produit le même output JSON
