# Otomata Tools

CLI et librairie Python pour l'automatisation : Google Workspace, Notion, Sirene (entreprises françaises), et plus.

## Installation

```bash
# CLI uniquement
pipx install git+https://github.com/AlexisLaporte/otomata-tools.git

# Dans un projet Python (dernière version)
pip install git+https://github.com/AlexisLaporte/otomata-tools.git

# Pinner une version
pip install git+https://github.com/AlexisLaporte/otomata-tools.git@v0.2.0

# Avec extras
pip install "otomata[stock] @ git+https://github.com/AlexisLaporte/otomata-tools.git"
```

### Extras disponibles

| Extra | Description |
|-------|-------------|
| `browser` | Browser automation (Patchright) |
| `stock` | Sirene stock file (pyarrow, pandas) |
| `company-fr` | Sirene API client |
| `ai` | Anthropic SDK |
| `all` | Tous les extras |

## Configuration des secrets

### Mode CLI

Les secrets sont lus depuis des fichiers `.otomata/secrets.env` :

1. **Projet** : `.otomata/secrets.env` dans le répertoire courant ou parents
2. **User** : `~/.otomata/secrets.env`

```bash
# Créer le fichier user
mkdir -p ~/.otomata
cat > ~/.otomata/secrets.env << 'EOF'
SIRENE_API_KEY=xxx
GROQ_API_KEY=xxx
GOOGLE_SERVICE_ACCOUNT='{"type":"service_account",...}'
NOTION_API_KEY=secret_xxx
EOF
```

### Mode librairie

Passer les secrets explicitement :

```python
from otomata.tools.sirene import SireneClient

client = SireneClient(api_key="xxx")  # Pas de magie, l'appelant gère ses secrets
```

## Sirene - Entreprises françaises

### CLI

```bash
# Recherche entreprises (API INSEE)
otomata sirene search --naf 62.01Z --employees 11,12 --limit 10

# Détails entreprise
otomata sirene get 443061841
otomata sirene siret 44306184100047
otomata sirene headquarters 443061841

# Suggestion codes NAF (IA)
otomata sirene suggest-naf "développement logiciel SaaS"

# Recherche enrichie (dirigeants, finances) - API data.gouv
otomata sirene entreprises "unitag" --ca-min 100000

# Stock file (~2GB, batch local)
otomata sirene stock status
otomata sirene stock download
otomata sirene stock addresses 443061841,552032534
```

### Librairie

```python
from otomata.tools.sirene import SireneClient, EntreprisesClient, SireneStock

# API INSEE Sirene
client = SireneClient(api_key="xxx")
results = client.search(naf=["62.01Z"], employees=["11", "12"], limit=50)
company = client.get_by_siren("443061841")
hq = client.get_headquarters("443061841")

# API Recherche Entreprises (data.gouv) - pas de clé requise
entreprises = EntreprisesClient()
results = entreprises.search(query="unitag", ca_min=100000)
directors = entreprises.get_directors("443061841")

# Stock file (batch, ~2GB local)
stock = SireneStock()
stock.download()  # Une fois, télécharge ~2GB
addresses = stock.get_headquarters_addresses(["443061841", "552032534"])
```

### NAF Suggester

```python
from otomata.tools.groq import GroqClient
from otomata.tools.naf import NAFSuggester

groq = GroqClient(api_key="xxx")
suggester = NAFSuggester(groq_client=groq)
suggestions = suggester.suggest("restaurant italien", limit=3)

for s in suggestions:
    print(f"{s.code} - {s.label} ({s.confidence:.0%})")
```

## Google Workspace

```bash
otomata google drive-list --folder-id=xxx
otomata google drive-download <file-id> output.pdf
otomata google docs-headings <doc-id>
```

```python
from otomata.tools.google.drive.lib.drive_client import DriveClient

drive = DriveClient()  # Utilise GOOGLE_SERVICE_ACCOUNT
files = drive.list_files(folder_id="xxx")
```

## Notion

```bash
otomata notion search "query"
otomata notion page <page-id> --blocks
otomata notion database <db-id> --query
```

```python
from otomata.tools.notion.lib.notion_client import NotionClient

notion = NotionClient()  # Utilise NOTION_API_KEY
results = notion.search("query")
```

## Browser automation

Pour les sites sans API publique (LinkedIn, Crunchbase, etc.) :

```python
from otomata.tools.browser import BrowserClient

async with BrowserClient(profile_path="~/.otomata/sessions/linkedin") as browser:
    await browser.goto("https://linkedin.com")
    # Session cookies persistés dans profile_path
```

## Versioning

La version est définie dans `otomata/__init__.py` (`__version__`). `pyproject.toml` la lit dynamiquement via hatchling.

Au premier import, otomata vérifie en arrière-plan si une nouvelle version existe sur GitHub (API releases, timeout 3s, non-bloquant). Si oui, un `warnings.warn` s'affiche avec la commande d'upgrade.

Désactiver le check :

```bash
OTOMATA_NO_UPDATE_CHECK=1 python mon_script.py
```

### Publier une nouvelle version

```bash
# 1. Bumper __version__ dans otomata/__init__.py
# 2. Commit + push
# 3. Tag + release
git tag v0.X.0
git push origin v0.X.0
gh release create v0.X.0 --title "v0.X.0" --notes "..."
```

## Développement

```bash
git clone https://github.com/AlexisLaporte/otomata-tools.git
cd otomata-tools
pip install -e ".[dev,all]"

# Vérifier config
otomata config
```
